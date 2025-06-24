from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import os
import uuid
import re

app = Flask(__name__)
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIE_FILE = 'cookies.txt'  # 若你導出 cookies，放在專案目錄下

def download_audio(url, format_choice):
    uid = str(uuid.uuid4())[:8]
    output_template = os.path.join(DOWNLOAD_DIR, f"{uid}_%(title).80s.%(ext)s")

    ydl_opts = {
        'outtmpl': output_template,
        'quiet': True,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format_choice,
            'preferredquality': '192' if format_choice == 'mp3' else None,
        }]
    }

    if os.path.exists(COOKIE_FILE):
        ydl_opts['cookiefile'] = COOKIE_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            downloaded_path = re.sub(r'\.[^.]+$', f'.{format_choice}', filename)

        return {
            'status': 'success',
            'title': info.get('title'),
            'download_url': f'/download/{os.path.basename(downloaded_path)}'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json()
    url = data.get('url')
    format_choice = data.get('format', 'mp3')

    if not url:
        return jsonify({'status': 'error', 'message': '未提供連結'})
    
    result = download_audio(url, format_choice)
    return jsonify(result)

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return 'File not found', 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
