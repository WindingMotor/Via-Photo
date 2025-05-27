# ViaPhoto 📸

### This project is currently in active development!

A modern, responsive photo upload gallery with a dark orange theme. ViaPhoto allows you to easily upload, view, and manage your photos with a clean, intuitive local interface.

Mobile and Desktop apps to come soon! 
## Features

- **Instant Photo Upload**: Drag and drop or select photos to upload instantly
- **Responsive Gallery**: View your photos in a grid layout
- **Smart Sorting**: Sort your photos by date, name, or size with a single click
- **Mobile-Friendly**: Fully responsive design that works great on phones and tablets

## Installation

### Prerequisites

- Python 3.7+
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/WindingMotor/Via-Photo
   cd viaphoto
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create uploads directory:
   ```bash
   mkdir -p uploads
   ```

## Usage

1. Start the server:
   ```bash
   python server.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8080
   ```

3. Upload photos by dragging and dropping them onto the upload area or by clicking to select files.

4. Click the "View Gallery" button to see your uploaded photos.

5. In the gallery, use the sorting dropdown to organize your photos by date, name, or size.

## Project Structure

```
viaphoto/
├── server.py              # Main server application
├── static/                # Static assets
│   ├── css/               # CSS stylesheets
│   ├── js/                # JavaScript files
│   └── img/               # Images and icons
├── templates/             # HTML templates
│   ├── upload_page.html   # Upload interface
│   ├── gallery.html       # Gallery view
│   └── error.html         # Error page
├── uploads/               # Uploaded photos (created at runtime)
└── requirements.txt       # Python dependencies
```

## Dependencies

- **aiohttp**: Asynchronous HTTP server
- **aiofiles**: Asynchronous file operations
- **jinja2**: HTML templating
- **aiohttp_jinja2**: Jinja2 integration for aiohttp

## Customization

### Changing Theme Colors

The primary theme color can be modified in `static/css/styles.css`:

```css
:root {
    --primary-color: #ff8c00;  /* Change this to your preferred color */
    --primary-dark: #e67e00;
    --primary-light: #ffa333;
    /* ... other variables ... */
}
```

### Modifying Gallery Layout

The gallery grid layout can be adjusted in `static/css/gallery.css`:

```css
.gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 20px;
    /* ... other properties ... */
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

