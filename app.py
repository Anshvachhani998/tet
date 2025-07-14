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





from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

class SpotMate:
    def __init__(self):
        self.session = requests.Session()
        self._token = None

    def _visit(self):
        headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36',
        }
        response = self.session.get('https://spotmate.online/en', headers=headers)
        response.raise_for_status()

        # Extract token
        soup = BeautifulSoup(response.text, 'html.parser')
        token = soup.find('meta', {'name': 'csrf-token'})
        if not token:
            raise Exception('Token CSRF tidak ditemukan.')
        self._token = token['content']

    def _get_headers(self):
        return {
            'accept': '*/*',
            'content-type': 'application/json',
            'origin': 'https://spotmate.online',
            'referer': 'https://spotmate.online/en',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36',
            'x-csrf-token': self._token,
        }

    def info(self, spotify_url):
        if not self._token:
            self._visit()

        payload = {'spotify_url': spotify_url}
        response = self.session.post('https://spotmate.online/getTrackData', json=payload, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def convert(self, spotify_url):
        if not self._token:
            self._visit()

        payload = {'urls': spotify_url}
        response = self.session.post('https://spotmate.online/convert', json=payload, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def clear(self):
        self.session.close()
        self._token = None

@app.route('/spotify2', methods=['GET'])
def spotify2():
    url = request.args.get('url')
    if not url:
        return jsonify({'status': False, 'error': 'Url is required'}), 400
    try:
        spotmate = SpotMate()
        track_info = spotmate.info(url)
        convert_result = spotmate.convert(url)

        result = {
            'status': True,
            'data': {
                'url': convert_result.get('url'),
                'title': track_info.get('album', {}).get('name')
            }
        }

        spotmate.clear()
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
