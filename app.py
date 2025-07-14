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
        raise ValueError("❌ Error: URL is missing!")

    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://spotiydownloader.com',
        'Referer': 'https://spotiydownloader.com/id',
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        meta_response = requests.post(
            'https://spotiydownloader.com/api/metainfo',
            json={'url': url},
            headers=headers,
            timeout=15
        )
        meta_response.raise_for_status()
    except requests.RequestException as e:
        raise ConnectionError(f"❌ Error fetching meta info: {e}")

    meta = meta_response.json()
    if not meta.get('success') or not meta.get('id'):
        raise ValueError("❌ Failed to get song info. Maybe wrong URL?")

    try:
        dl_response = requests.post(
            'https://spotiydownloader.com/api/download',
            json={'id': meta['id']},
            headers=headers,
            timeout=15
        )
        dl_response.raise_for_status()
    except requests.RequestException as e:
        raise ConnectionError(f"❌ Error fetching download link: {e}")

    result = dl_response.json()
    if not result.get('success') or not result.get('link'):
        raise ValueError("❌ Failed to get download link.")

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
        return jsonify({'status': False, 'error': '❌ URL is required!'}), 400

    try:
        data = spotify_download(url)
        return jsonify({'status': True, 'data': data}), 200
    except ValueError as ve:
        return jsonify({'status': False, 'error': str(ve)}), 400
    except ConnectionError as ce:
        return jsonify({'status': False, 'error': str(ce)}), 502
    except Exception as e:
        return jsonify({'status': False, 'error': f"❌ Unexpected error: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': False, 'error': '❌ Endpoint not found.'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'status': False, 'error': '❌ Method not allowed.'}), 405

if __name__ == '__main__':
    app.run(debug=True)
