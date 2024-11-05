from flask import Flask, request, send_file, render_template
import yt_dlp
import os
import re
import subprocess
import threading
import time
import tempfile

app = Flask(__name__)
base_path = "./%(title)s.%(ext)s"  

@app.route('/')
def home():
    return render_template('index.html') 

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    quality = request.form.get('quality')

    if not url or not quality:
        return "Please provide both a URL and a quality option.", 400

    quality_mapping = {
        '360p': 360,
        '480p': 480,
        '720p': 720,
        '1080p': 1080,
        '1440p': 1440,
        '4K': 2160,
        'Highest': 'best',
        'Audio Only': 'bestaudio'
    }

    try:
        with yt_dlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            title = sanitize_title(info_dict.get('title', 'video'))

        # Define file paths in a temporary directory
        video_file = os.path.join(tempfile.gettempdir(), f"{title}.mp4")
        audio_file = os.path.join(tempfile.gettempdir(), f"{title}.m4a")
        final_file = os.path.join(tempfile.gettempdir(), f"{title}_final.mp4")

        video_ydl_opts = {
            'format': f'bestvideo[height<={quality_mapping[quality]}]',
            'outtmpl': video_file,
            'no_color': True,
            'noplaylist': True,
        }
        audio_ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': audio_file,
            'no_color': True,
            'noplaylist': True,
        }

        # Download video and audio
        with yt_dlp.YoutubeDL(video_ydl_opts) as video_ydl:
            video_ydl.download([url])
        with yt_dlp.YoutubeDL(audio_ydl_opts) as audio_ydl:
            audio_ydl.download([url])

        # Merge files using FFmpeg
        merge_files(video_file, audio_file, final_file)

        response = send_file(final_file, as_attachment=True, download_name=f"{title}.mp4")

        # Start a background thread to delete the file after a short delay
        threading.Thread(target=delete_file, args=[final_file]).start()

        return response

    except Exception as e:
        return f"Error: {str(e)}", 500

def sanitize_title(title):
    title = re.sub(r'[^\w\s-]', '', title)
    title = re.sub(r'[-\s]+', '_', title)
    return title.strip('_')

def merge_files(video_file, audio_file, final_file):
    ffmpeg_command = f'ffmpeg -i "{video_file}" -i "{audio_file}" -c:v copy -c:a aac -strict experimental "{final_file}"'
    subprocess.run(ffmpeg_command, shell=True, check=True)
    os.remove(video_file)
    os.remove(audio_file)

def delete_file(filepath):
    time.sleep(5)  
    if os.path.exists(filepath):
        os.remove(filepath)

if __name__ == "__main__":
    app.run(debug=True)
