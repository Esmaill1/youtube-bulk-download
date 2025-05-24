# YouTube Video Downloader

A modern, responsive web interface for downloading YouTube videos with various quality options, bulk downloading, and more.

## Features

- **Quality Selection**: Choose from various video quality options including 1080p, 720p, 480p, and more.
- **Bulk Download**: Download multiple videos at once by entering URLs on separate lines.
- **Cookies Support**: Optionally upload cookies to download private or restricted videos.
- **Thumbnail Preview**: See a preview of the video before downloading.
- **Dark/Light Theme**: Toggle between dark and light themes for comfortable viewing.
- **Modern Design**: Elegant, responsive design with smooth animations.

## Requirements

- Python 3.7+
- yt-dlp (must be installed and accessible in PATH)

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd youtube-video-downloader
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Install yt-dlp (if not already installed):
   ```
   pip install yt-dlp
   ```

## Usage

1. Start the web server:
   ```
   python app.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. Enter a YouTube URL, optionally upload cookies, select quality, and download!

## Bulk Download

1. Switch to the "Bulk Download" tab.
2. Enter multiple YouTube URLs, one per line.
3. Select a quality that will apply to all videos.
4. Click "Download All".

## Notes

- Downloaded files are saved to the `downloads` directory.
- Supported cookies file formats: .txt and .json
- For private or geo-restricted videos, you may need to provide cookies from a browser. 