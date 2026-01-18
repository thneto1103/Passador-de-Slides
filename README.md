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
1. A dialog will appear asking you to select the "Photos" folder
2. Select the folder containing your photo subfolders
3. The slideshow will start automatically

## Controls

- **ESC**: Exit fullscreen or quit application
- **SPACE**: Pause/Resume slideshow
- **R**: Toggle between Sequential and Random mode
- **← (Left Arrow)**: Previous image
- **→ (Right Arrow)**: Next image
- **F**: Toggle fullscreen mode

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
