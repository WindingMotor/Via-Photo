const fileInput = document.getElementById('photos');
const uploadBtn = document.getElementById('uploadBtn');
const uploadZone = document.getElementById('uploadZone');
const speedDisplay = document.getElementById('speedDisplay');
const speedValue = document.getElementById('speedValue');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const photoQueue = document.getElementById('photoQueue');
const queueList = document.getElementById('queueList');
const queueSummary = document.getElementById('queueSummary');
const statsGrid = document.getElementById('statsGrid');
const results = document.getElementById('results');

let selectedFiles = [];
let uploadStartTime = 0;
let lastProgressTime = 0;
let lastProgressLoaded = 0;
let uploadedCount = 0;

// Enhanced drag and drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    uploadZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

['dragenter', 'dragover'].forEach(eventName => {
    uploadZone.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    uploadZone.addEventListener(eventName, unhighlight, false);
});

uploadZone.addEventListener('drop', handleDrop, false);

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight() {
    uploadZone.classList.add('dragover');
}

function unhighlight() {
    uploadZone.classList.remove('dragover');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    fileInput.files = files;
    handleFileSelection();
}

fileInput.addEventListener('change', handleFileSelection);

function handleFileSelection() {
    selectedFiles = Array.from(fileInput.files);
    updatePhotoQueue();
    updateUploadButton();
}

function updatePhotoQueue() {
    if (selectedFiles.length === 0) {
        photoQueue.style.display = 'none';
        return;
    }
    
    photoQueue.style.display = 'block';
    let html = '';
    
    let totalSize = 0;
    selectedFiles.forEach((file, index) => {
        const sizeMB = (file.size / 1024 / 1024).toFixed(2);
        totalSize += file.size;
        
        html += `
            <div class="photo-item status-waiting" id="photo-${index}">
                <div class="photo-info">
                    <div class="photo-name">${file.name}</div>
                    <div class="photo-size">${sizeMB} MB</div>
                </div>
                <div class="photo-status status-waiting" id="status-${index}">Waiting</div>
            </div>
        `;
    });
    
    queueList.innerHTML = html;
    
    const totalSizeMB = (totalSize / 1024 / 1024).toFixed(1);
    queueSummary.textContent = `${selectedFiles.length} photos • ${totalSizeMB} MB total`;
}

function updateUploadButton() {
    if (selectedFiles.length === 0) {
        uploadBtn.textContent = 'Select Photos First';
        uploadBtn.disabled = true;
    } else {
        const totalSize = selectedFiles.reduce((sum, file) => sum + file.size, 0);
        const totalSizeMB = (totalSize / 1024 / 1024).toFixed(1);
        uploadBtn.textContent = `Upload ${selectedFiles.length} Photos (${totalSizeMB} MB)`;
        uploadBtn.disabled = false;
    }
}

function updatePhotoStatus(index, status, statusText) {
    const photoItem = document.getElementById(`photo-${index}`);
    const statusElement = document.getElementById(`status-${index}`);
    
    if (photoItem && statusElement) {
        // Remove old status classes
        photoItem.className = photoItem.className.replace(/status-\w+/g, '');
        statusElement.className = statusElement.className.replace(/status-\w+/g, '');
        
        // Add new status
        photoItem.classList.add(`status-${status}`);
        statusElement.classList.add(`status-${status}`);
        statusElement.textContent = statusText;
        
        // Scroll item into view
        photoItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// Simulate individual photo upload completion
function simulatePhotoUploads(totalFiles) {
    uploadedCount = 0;
    
    // Mark all as uploading first
    for (let i = 0; i < totalFiles; i++) {
        updatePhotoStatus(i, 'uploading', 'Uploading');
    }
    
    // Simulate individual completions based on file sizes
    let completedFiles = 0;
    const interval = setInterval(() => {
        if (completedFiles < totalFiles) {
            updatePhotoStatus(completedFiles, 'uploaded', 'Uploaded');
            completedFiles++;
            uploadedCount = completedFiles;
            
            // Update uploaded count in stats
            document.getElementById('uploadedFiles').textContent = uploadedCount;
        } else {
            clearInterval(interval);
        }
    }, Math.max(100, (30000 / totalFiles))); // Spread over upload time
}

uploadBtn.addEventListener('click', startUpload);

async function startUpload() {
    if (selectedFiles.length === 0) return;
    
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Uploading...';
    
    speedDisplay.style.display = 'block';
    progressContainer.style.display = 'block';
    statsGrid.style.display = 'grid';
    
    uploadedCount = 0;
    
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('photos', file);
    });
    
    uploadStartTime = Date.now();
    lastProgressTime = uploadStartTime;
    lastProgressLoaded = 0;
    
    // Start simulating individual photo uploads
    simulatePhotoUploads(selectedFiles.length);
    
    try {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                progressBar.style.width = percent + '%';
                progressText.textContent = `${percent.toFixed(1)}% uploaded`;
                
                const now = Date.now();
                const elapsed = (now - uploadStartTime) / 1000;
                const totalSpeedMBps = (e.loaded / (1024 * 1024)) / elapsed;
                
                // Calculate instantaneous speed
                const timeDiff = (now - lastProgressTime) / 1000;
                const dataDiff = e.loaded - lastProgressLoaded;
                const instantSpeedMBps = (dataDiff / (1024 * 1024)) / timeDiff;
                
                if (timeDiff > 0.1) { // Update every 100ms
                    speedValue.textContent = Math.max(totalSpeedMBps, instantSpeedMBps).toFixed(1);
                    lastProgressTime = now;
                    lastProgressLoaded = e.loaded;
                }
                
                // Update stats
                document.getElementById('uploadedSize').textContent = `${(e.loaded / 1024 / 1024).toFixed(1)} MB`;
                document.getElementById('timeElapsed').textContent = `${elapsed.toFixed(1)}s`;
                document.getElementById('throughput').textContent = `${totalSpeedMBps.toFixed(1)} MB/s`;
            }
        });
        
        xhr.onload = function() {
            if (xhr.status === 200) {
                // Ensure all photos show as uploaded
                for (let i = 0; i < selectedFiles.length; i++) {
                    updatePhotoStatus(i, 'uploaded', 'Uploaded');
                }
                
                document.getElementById('uploadedFiles').textContent = selectedFiles.length;
                results.innerHTML = xhr.responseText;
                
                // Auto-reset after 5 seconds
                setTimeout(() => {
                    resetUploadInterface();
                }, 5000);
                
            } else {
                results.innerHTML = '<div style="color: #ff6b6b; text-align: center; padding: 20px;">❌ Upload failed. Check saved photos in directory.</div>';
            }
            
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload More Photos';
        };
        
        xhr.onerror = () => {
            results.innerHTML = '<div style="color: #ff6b6b; text-align: center; padding: 20px;">❌ Network error. Check saved photos in directory.</div>';
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Try Again';
        };
        
        xhr.open('POST', '/upload');
        xhr.send(formData);
        
    } catch (error) {
        results.innerHTML = `<div style="color: #ff6b6b; text-align: center; padding: 20px;">❌ Error: ${error.message}</div>`;
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Try Again';
    }
}

function resetUploadInterface() {
    speedDisplay.style.display = 'none';
    progressContainer.style.display = 'none';
    statsGrid.style.display = 'none';
    photoQueue.style.display = 'none';
    
    fileInput.value = '';
    selectedFiles = [];
    updateUploadButton();
    
    progressBar.style.width = '0%';
    progressText.textContent = 'Ready to upload';
    results.innerHTML = '';
}
