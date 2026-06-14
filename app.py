from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import tempfile
import uuid
import os

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = tempfile.gettempdir()

@app.route('/formats', methods=['POST'])
def get_formats():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL'}), 400
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    formats = []
    for f in info.get('formats', []):
        height = f.get('height')
        if height == 1080 and f.get('vcodec') != 'none':
            formats.append({
                'format_id': f['format_id'],
                'ext': f['ext'],
                'resolution': f'{height}p',
                'filesize': f.get('filesize'),
                'has_audio': f.get('acodec') != 'none'
            })
    return jsonify({
        'title': info.get('title'),
        'thumbnail': info.get('thumbnail'),
        'formats': formats
    })

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data['url']
    format_id = data['format_id']
    job_id = str(uuid.uuid4())
    outtmpl = os.path.join(DOWNLOAD_DIR, f'{job_id}.%(ext)s')
    ydl_opts = {
    'outtmpl': outtmpl,
    'quiet': True,
    'format': format_id,
    'merge_output_format': 'mp4',
    'extractor_args': {
        'youtube': {
            'po_token': [f'{os.getenv("PO_TOKEN_PROVIDER_URL")}/web'],
        }
    }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    for f in os.listdir(DOWNLOAD_DIR):
        if f.startswith(job_id):
            return send_file(os.path.join(DOWNLOAD_DIR, f), as_attachment=True)
    return jsonify({'error': 'File not found'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
