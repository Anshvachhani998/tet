from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

def ms_to_minutes(ms):
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{str(seconds).zfill(2)}"

def spotify_download(url):
    if not url:
        raise ValueError("Link-nya mana, senpai?")

    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://spotiydownloader.com',
        'Referer': 'https://spotiydownloader.com/id',
        'User-Agent': 'Mozilla/5.0'
    }

    meta_response = requests.post(
        'https://spotiydownloader.com/api/metainfo',
        json={'url': url},
        headers=headers
    )

    meta = meta_response.json()
    if not meta or not meta.get('success') or not meta.get('id'):
        raise ValueError('Gomen senpai! Aku gagal mengambil info lagunya')

    dl_response = requests.post(
        'https://spotiydownloader.com/api/download',
        json={'id': meta['id']},
        headers=headers
    )

    result = dl_response.json()
    if not result or not result.get('success') or not result.get('link'):
        raise ValueError('Yabai! Gagal dapetin link-nya senpai!')

    return {
        'artist': meta.get('artists') or meta.get('artist') or 'Unknown',
        'title': meta.get('title') or 'Unknown',
        'duration': ms_to_minutes(meta['duration_ms']) if meta.get('duration_ms') else 'Unknown',
        'image': meta.get('cover'),
        'download': result['link']
    }

@app.route('/spotify', methods=['GET'])
def spotify_route():
    url = request.args.get('url')
    if not url:
        return jsonify({'status': False, 'error': 'Url is required'}), 400

    try:
        data = spotify_download(url)
        return jsonify({'status': True, 'data': data}), 200
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
