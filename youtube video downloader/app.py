import os
import subprocess
import json
import tempfile
from flask import Flask, render_template, request, jsonify, url_for, redirect, send_from_directory
from werkzeug.utils import secure_filename
import requests
import re

app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'json'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_video_info(url, cookies_file=None):
    """Get information about the video using yt-dlp"""
    cmd = ["yt-dlp", "--dump-json", url]
    
    if cookies_file:
        cmd.extend(["--cookies", cookies_file])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return {"error": result.stderr}
        
        video_info = json.loads(result.stdout)
        return {
            "title": video_info.get("title", "Unknown"),
            "thumbnail": video_info.get("thumbnail", ""),
            "duration": video_info.get("duration", 0),
            "formats": [
                {
                    "format_id": fmt.get("format_id", ""),
                    "ext": fmt.get("ext", ""),
                    "resolution": fmt.get("resolution", ""),
                    "format_note": fmt.get("format_note", ""),
                    "vcodec": fmt.get("vcodec", ""),
                    "acodec": fmt.get("acodec", "")
                }
                for fmt in video_info.get("formats", [])
                if not fmt.get("format_id", "").startswith("sb")  # Skip storyboard formats
            ]
        }
    except Exception as e:
        return {"error": str(e)}

def download_with_cli(url, format_id=None, cookies_file=None, output_dir=None):
    """Download video using yt-dlp CLI"""
    # Prepare command
    cmd = ["yt-dlp"]
    
    if format_id:
        cmd.extend(["-f", format_id])
    
    if cookies_file:
        cmd.extend(["--cookies", cookies_file])
    
    if output_dir:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        cmd.extend(["-P", output_dir])
    
    cmd.append(url)
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output_lines = []
        for line in process.stdout:
            output_lines.append(line)
        process.wait()
        
        return {
            "success": process.returncode == 0,
            "output": "".join(output_lines)
        }
    except Exception as e:
        return {
            "success": False,
            "output": str(e)
        }

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def download_thumbnail(video_id, path):
    """Download thumbnail for a video ID"""
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    thumbnail_path = os.path.join(path, f"{video_id}.jpg")
    
    try:
        response = requests.get(thumbnail_url)
        if response.status_code == 404:
            # Try the medium quality thumbnail if maxres doesn't exist
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
            response = requests.get(thumbnail_url)
        
        with open(thumbnail_path, 'wb') as f:
            f.write(response.content)
        
        return f"/uploads/thumbnails/{video_id}.jpg"
    except Exception:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_video_info', methods=['POST'])
def api_get_video_info():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    cookies_file = None
    if 'cookies' in request.files and request.files['cookies'].filename:
        file = request.files['cookies']
        if allowed_file(file.filename):
            cookies_file = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(cookies_file)
    
    video_info = get_video_info(url, cookies_file)
    
    # Download thumbnail
    video_id = extract_video_id(url)
    if video_id:
        thumbnail_path = download_thumbnail(
            video_id, 
            os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails')
        )
        if thumbnail_path:
            video_info['local_thumbnail'] = thumbnail_path
    
    return jsonify(video_info)

@app.route('/download', methods=['POST'])
def api_download():
    url = request.form.get('url')
    format_id = request.form.get('format_id')
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    cookies_file = None
    if 'cookies' in request.files and request.files['cookies'].filename:
        file = request.files['cookies']
        if allowed_file(file.filename):
            cookies_file = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(cookies_file)
    
    output_dir = "downloads"
    result = download_with_cli(url, format_id, cookies_file, output_dir)
    
    return jsonify(result)

@app.route('/bulk_download', methods=['POST'])
def api_bulk_download():
    if 'urls' not in request.form:
        return jsonify({"error": "No URLs provided"}), 400
    
    urls = request.form.get('urls').strip().split('\n')
    format_id = request.form.get('format_id')
    
    cookies_file = None
    if 'cookies' in request.files and request.files['cookies'].filename:
        file = request.files['cookies']
        if allowed_file(file.filename):
            cookies_file = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(cookies_file)
    
    output_dir = "downloads"
    results = []
    
    for url in urls:
        url = url.strip()
        if url:
            result = download_with_cli(url, format_id, cookies_file, output_dir)
            results.append({
                "url": url,
                "success": result["success"],
                "output": result["output"]
            })
    
    return jsonify({"results": results})

@app.route('/uploads/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails'), filename)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000) 