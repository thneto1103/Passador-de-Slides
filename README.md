# Photo Slide Show

A Python application for displaying photos from a folder structure in sequential or random mode.

## Features

- **Sequential Mode**: Displays photos in order (first from first folder, then second, etc.)
- **Random Mode**: Randomly selects and displays photos from the entire folder structure
- **Fullscreen Display**: Full-screen presentation mode
- **Smooth Transitions**: Clean transitions between images
- **Keyboard Controls**: Easy navigation with keyboard shortcuts

## Folder Structure

The application expects a folder structure like:

```
Photos/
├── photos2003/
│   ├── image1.jpg
│   ├── image2.jpg
│   └── ...
├── campPhotos/
│   ├── photo1.jpg
│   └── ...
└── ...
```

## Installation

1. Install Python 3.7 or higher
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application:

```bash
python slide_show.py
```

When the application starts:
1. A dialog will appear asking you to select photo folder(s)
2. Select one or more folders containing your photos (subfolders are automatically scanned)
3. The slideshow will start automatically

## Building an Executable

You can create a standalone executable that runs without Python installed.

### Windows

1. Open Command Prompt or PowerShell in the project folder
2. Run the build script:

```bash
build_executable.bat
```

Or manually:

```bash
pip install pyinstaller
pyinstaller --name="PhotoSlideShow" --onefile --windowed --hidden-import=PIL --hidden-import=PIL.Image --hidden-import=PIL.ImageTk slide_show.py
```

The executable will be in the `dist` folder: `dist\PhotoSlideShow.exe`

### Linux/Mac

1. Open Terminal in the project folder
2. Make the script executable (first time only):

```bash
chmod +x build_executable.sh
```

3. Run the build script:

```bash
./build_executable.sh
```

Or manually:

```bash
pip install pyinstaller
pyinstaller --name="PhotoSlideShow" --onefile --windowed --hidden-import=PIL --hidden-import=PIL.Image --hidden-import=PIL.ImageTk slide_show.py
```

The executable will be in the `dist` folder: `dist/PhotoSlideShow`

**Note**: The executable is standalone and can be distributed without Python. Just copy the `.exe` (Windows) or executable file (Linux/Mac) to any computer.

## Controls

### Buttons (Auto-hide on mouse inactivity)

- **← Previous**: Go to previous image
- **⏭ Auto [ON/OFF]**: Toggle automatic slideshow mode
- **⏸ Pause / ▶ Resume**: Pause/resume slideshow
- **🎲 Random**: Toggle random mode (randomly selects photos)
- **⛶ Fullscreen**: Toggle fullscreen mode
- **Next →**: Go to next image
- **✕ Quit**: Exit application

**Note**: Control buttons automatically hide after 3-4 seconds of mouse inactivity. Move the mouse to show them again.

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- BMP (.bmp)
- WebP (.webp)
- TIFF (.tiff, .tif)

## Customization

You can modify the display duration by changing the `display_duration` variable in the code (default: 3000 milliseconds = 3 seconds).

## Requirements

- Python 3.7+
- Pillow (PIL) library
- tkinter (usually included with Python)
