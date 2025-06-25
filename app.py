from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import os
import uuid
import re
import zipfile
import shutil
import tempfile

app = Flask(__name__)

# Cookies 檔案路徑
COOKIE_PATH = os.path.join(os.getcwd(), 'cookie.txt')

def download_audio(url, format_choice, download_dir):
    uid = str(uuid.uuid4())[:8]
    output_template = os.path.join(download_dir, f"{uid}_%(title).80s.%(ext)s")

    ydl_opts = {
        'outtmpl': output_template,
        'quiet': True,
        'format': 'bestaudio/best',
        'cookiefile': COOKIE_PATH if os.path.exists(COOKIE_PATH) else None,
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
            downloaded_path = re.sub(r'\.[^.]+$', f'.{format_choice}', filename)
        return {
            'status': 'success',
            'title': info.get('title'),
            'filepath': downloaded_path
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e), 'url': url}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json()
    raw_urls = data.get('url', '')
    format_choice = data.get('format', 'mp3')

    if not raw_urls:
        return jsonify({'status': 'error', 'message': '請提供至少一個 URL'})

    urls = [url.strip() for url in raw_urls.strip().splitlines() if url.strip()]
    results = []
    success_files = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for url in urls:
            result = download_audio(url, format_choice, tmpdir)
            results.append(result)
            if result['status'] == 'success':
                success_files.append(result['filepath'])

        if not success_files:
            return jsonify({'status': 'error', 'message': '所有連結皆下載失敗', 'results': results})

        if len(success_files) == 1:
            file = success_files[0]
            final_path = os.path.join('downloads', os.path.basename(file))
            shutil.move(file, final_path)
            return jsonify({
                'status': 'single',
                'download_url': f'/download/{os.path.basename(file)}',
                'results': results
            })

        zip_name = f"downloads_{uuid.uuid4().hex[:8]}.zip"
        zip_path = os.path.join(tmpdir, zip_name)

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file in success_files:
                arcname = os.path.basename(file)
                zipf.write(file, arcname=arcname)

        final_zip_path = os.path.join('downloads', zip_name)
        shutil.move(zip_path, final_zip_path)

        return jsonify({
            'status': 'zip',
            'zip_url': f'/download/{zip_name}',
            'results': results
        })

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join('downloads', filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return 'File not found', 404

if __name__ == '__main__':
    os.makedirs('downloads', exist_ok=True)
    app.run(debug=True, host='0.0.0.0')
