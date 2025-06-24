from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import os
import uuid
import re

app = Flask(__name__)

# 建立下載資料夾
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(filename)
            downloaded_path = f"{base}.{format_choice}"

        return {
            'status': 'success',
            'title': info.get('title'),
            'download_url': f'/download/{os.path.basename(downloaded_path)}'
        }

    except Exception as e:
        print(f"[ERROR] {e}")  # 加入錯誤輸出
        return {'status': 'error', 'message': str(e)}

# 首頁載入 HTML
@app.route('/')
def index():
    return render_template('index.html')

# 音訊下載 API
@app.route('/api/download', methods=['POST'])
def api_download():
    if request.is_json:
        data = request.get_json()
        url = data.get('url')
        format_choice = data.get('format', 'mp3')

        if not url:
            return jsonify({'status': 'error', 'message': 'URL 未提供'})

        result = download_audio(url, format_choice)
        return jsonify(result)
    else:
        return jsonify({'status': 'error', 'message': '請使用 JSON 格式'}), 400

# 檔案下載路由
@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return 'File not found', 404

# 本地測試用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
