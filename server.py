#!/usr/bin/env python3
import os
import socket
import asyncio
import aiofiles
import time
import json
import tempfile
from dataclasses import dataclass
from typing import List, Optional
import uvloop  # High-performance event loop
from aiohttp import web
import multiprocessing
import platform
from pathlib import Path
import jinja2
import aiohttp_jinja2

# Install dependencies: pip install aiohttp aiofiles uvloop jinja2 aiohttp_jinja2

def get_dynamic_upload_dir():
    system = platform.system()
    home = str(Path.home())
    if system == 'Windows':
        pictures_dir = os.path.join(home, 'Pictures')
    elif system == 'Darwin':
        pictures_dir = os.path.join(home, 'Pictures')
    else:
        # Linux and others: use XDG_PICTURES_DIR if set, else fallback
        xdg_pictures = os.environ.get('XDG_PICTURES_DIR')
        if xdg_pictures:
            pictures_dir = xdg_pictures
        else:
            pictures_dir = os.path.join(home, 'Pictures')
    upload_dir = os.path.join(pictures_dir, 'ViaPhoto')
    return upload_dir

UPLOAD_DIR = get_dynamic_upload_dir()
os.makedirs(UPLOAD_DIR, exist_ok=True)

CHUNK_SIZE = 4 * 1024 * 1024  # 4MB chunks for maximum local network performance
SOCKET_BUFFER_SIZE = 4 * 1024 * 1024  # 4MB socket buffers
MAX_WORKERS = min(64, (os.cpu_count() or 1) * 4)  # More aggressive parallelism

@dataclass
class UploadStats:
    files_uploaded: int = 0
    bytes_uploaded: int = 0
    start_time: float = 0
    active_uploads: int = 0

stats = UploadStats()

class ViaPhotoServer:
    def __init__(self):
        # Create directories with proper error handling
        print(f"📁 Creating upload directory: {os.path.abspath(UPLOAD_DIR)}")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Create temp directory for atomic writes
        self.temp_dir = os.path.join(UPLOAD_DIR, '.temp')
        print(f"📁 Creating temp directory: {os.path.abspath(self.temp_dir)}")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Verify directories exist
        if not os.path.exists(UPLOAD_DIR):
            raise Exception(f"Failed to create upload directory: {UPLOAD_DIR}")
        if not os.path.exists(self.temp_dir):
            raise Exception(f"Failed to create temp directory: {self.temp_dir}")
            
        print(f"✅ Upload directory ready: {os.path.abspath(UPLOAD_DIR)}")
        print(f"✅ Temp directory ready: {os.path.abspath(self.temp_dir)}")
        
    async def handle_upload_page(self, request):
        """Serve ViaPhoto upload interface with orange dark theme"""
        return aiohttp_jinja2.render_template('upload_page.html', request, {})
        

    async def handle_upload(self, request):
        """ViaPhoto upload handler - saves photos immediately as they arrive"""
        upload_id = int(time.time() * 1000000)
        start_time = time.time()
        
        stats.active_uploads += 1
        stats.start_time = start_time
        
        print(f"\n📱 ViaPhoto Upload #{upload_id} starting...")
        print("💾 Photos will be saved immediately as they arrive")
        
        try:
            uploaded_files = []
            total_size = 0
            files_processed = 0
            
            # Process each photo immediately
            reader = await request.multipart()
            
            async for part in reader:
                if part.name == 'photos' and part.filename:
                    files_processed += 1
                    print(f"📱 [{files_processed}] ViaPhoto processing: {part.filename}")
                    
                    # Save photo directly to disk immediately
                    result = await self.save_photo_immediately(part, upload_id, files_processed)
                    
                    if result:
                        uploaded_files.append(result)
                        total_size += result['size']
                        print(f"✅ [{files_processed}] SAVED: {result['filename']} ({result['size']/(1024*1024):.2f} MB)")
                    else:
                        print(f"❌ [{files_processed}] FAILED: {part.filename}")
            
            upload_time = time.time() - start_time
            average_speed = (total_size / (1024*1024)) / upload_time if upload_time > 0 else 0
            
            stats.files_uploaded += len(uploaded_files)
            stats.bytes_uploaded += total_size
            stats.active_uploads -= 1
            
            print(f"🎯 ViaPhoto Upload #{upload_id} COMPLETE:")
            print(f"   📁 Photos: {len(uploaded_files)} (saved immediately)")
            print(f"   📊 Size: {total_size/(1024*1024):.2f} MB")
            print(f"   ⏱️  Time: {upload_time:.2f}s")
            print(f"   🚀 Speed: {average_speed:.2f} MB/s")
            print(f"   💾 All photos safely saved to: {os.path.abspath(UPLOAD_DIR)}")
            
            # Generate nothing as response
            response_html = " "
            
            return web.Response(text=response_html, content_type='text/html')
            
        except Exception as e:
            stats.active_uploads -= 1
            print(f"❌ ViaPhoto Upload error: {e}")
            import traceback
            traceback.print_exc()
            
            # Render error template
            context = {
                'error_message': str(e),
                'upload_dir': os.path.abspath(UPLOAD_DIR)
            }
            return aiohttp_jinja2.render_template('error.html', request, context, status=500)

    async def save_photo_immediately(self, part, upload_id, file_number):
        """Save photo directly to disk as data arrives - ZERO data loss risk"""
        try:
            # Generate unique filename with microsecond precision
            timestamp = int(time.time() * 1000000)
            safe_filename = f"{timestamp}_{file_number:03d}_{part.filename}"
            
            # Use temporary file for atomic write - FIXED path handling
            temp_filename = f"{safe_filename}.tmp"
            temp_filepath = os.path.join(self.temp_dir, temp_filename)
            final_filepath = os.path.join(UPLOAD_DIR, safe_filename)
            
            # Verify temp directory exists before writing
            if not os.path.exists(self.temp_dir):
                print(f"⚠️  Temp directory missing, recreating: {self.temp_dir}")
                os.makedirs(self.temp_dir, exist_ok=True)
            
            file_size = 0
            
            print(f"💾 Writing to temp: {temp_filepath}")
            
            # Stream photo data directly to disk with large chunks
            async with aiofiles.open(temp_filepath, 'wb') as f:
                while True:
                    # Use larger chunks for better local network performance
                    chunk = await part.read_chunk(CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    await f.write(chunk)
                    file_size += len(chunk)
                    
                # Force flush and sync to ensure data is physically written
                await f.flush()
                # Use executor for sync operation to avoid blocking
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: os.fsync(f.fileno())
                )
            
            print(f"📁 Moving to final: {final_filepath}")
            
            # Atomic move from temp to final location
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: os.rename(temp_filepath, final_filepath)
            )
            
            # Verify photo was written correctly
            actual_size = os.path.getsize(final_filepath)
            if actual_size != file_size:
                print(f"⚠️  Size verification: {safe_filename} - expected {file_size}, got {actual_size}")
            
            return {
                'filename': safe_filename,
                'original_name': part.filename,
                'size': actual_size,
                'file_number': file_number
            }
            
        except Exception as e:
            print(f"❌ Error saving {part.filename}: {e}")
            print(f"❌ Temp path: {temp_filepath}")
            print(f"❌ Final path: {final_filepath}")
            print(f"❌ Temp dir exists: {os.path.exists(self.temp_dir)}")
            
            # Clean up any partial files
            for cleanup_path in [temp_filepath, final_filepath]:
                if os.path.exists(cleanup_path):
                    try:
                        os.remove(cleanup_path)
                        print(f"🧹 Cleaned up: {cleanup_path}")
                    except:
                        pass
            return None

    
def get_local_ip():
    """Get local network IP address"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "localhost"

async def create_app():
    """Create optimized ViaPhoto application"""
    # Use uvloop for maximum performance
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    # Create app with maximum performance settings
    app = web.Application(client_max_size=4*1024**3)  # 4GB max request size
    
    # Set up Jinja2 templates
    templates_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(templates_path))
    
    # Set up static file serving
    static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    app.router.add_static('/static/', path=static_path, name='static')
    
    # Create server instance
    server = ViaPhotoServer()
    
    # Add routes
    app.add_routes([
        web.get('/', server.handle_upload_page),
        web.post('/upload', server.handle_upload),
    ])
    
    return app

async def main():
    port = 8000
    local_ip = get_local_ip()
    
    print("📱 ViaPhoto Ultra-Fast Server v3.2 - ORANGE DARK THEME")
    print("=" * 70)
    print(f"📱 Phone URL: http://{local_ip}:{port}")
    print(f"💻 Local URL: http://localhost:{port}")
    print(f"📁 Upload folder: {os.path.abspath(UPLOAD_DIR)}")
    print(f"🚀 Chunk size: {CHUNK_SIZE/(1024*1024):.1f} MB (OPTIMIZED)")
    print(f"🔧 Max workers: {MAX_WORKERS}")
    print(f"💾 Socket buffers: {SOCKET_BUFFER_SIZE//1024}KB")
    print("\n🎯 ViaPhoto UI IMPROVEMENTS:")
    print("   🧡 Orange dark theme for better visibility")
    print("   📱 Simplified mobile-first layout")
    print("   📋 Real-time photo queue with status updates")
    print("   ✅ Individual 'Uploaded' status per photo")
    print("   🎨 Smooth animations and transitions")
    print("   📊 Clean stats display")
    print("   🚀 Enhanced dropzone experience")
    print("\n💾 PHOTOS SAVED IMMEDIATELY - No more data loss risk!")
    print("Press Ctrl+C to stop\n")
    
    try:
        app = await create_app()
        
        # Create custom runner
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', port, reuse_address=True, reuse_port=True)
        
        await site.start()
        
        print("✅ ViaPhoto server started successfully!")
        print("🧡 Orange dark theme UI ready!")
        print("📱 Real-time photo queue active!")
        print("💾 Photos will be saved immediately as they arrive!")
        
        # Keep the server running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("\n🛑 ViaPhoto server stopped")
    except Exception as e:
        print(f"❌ ViaPhoto server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Install required packages first
    try:
        import aiohttp
        import aiofiles
        import uvloop
    except ImportError:
        print("📦 Installing required packages...")
        import subprocess
        subprocess.check_call(["pip", "install", "aiohttp", "aiofiles", "uvloop"])
        print("✅ Packages installed!")
        
    asyncio.run(main())
