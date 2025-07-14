from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

def ms_to_minutes(ms):
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{str(seconds).zfill(2)}"

def spotify_primary(url):
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://spotiydownloader.com',
        'Referer': 'https://spotiydownloader.com/id',
        'User-Agent': 'Mozilla/5.0'
    }

    meta_response = requests.post(
        'https://spotiydownloader.com/api/metainfo',
        json={'url': url},
        headers=headers,
        timeout=15
    )
    meta_response.raise_for_status()
    meta = meta_response.json()

    if not meta.get('success') or not meta.get('id'):
        raise ValueError("Primary source: Failed to get meta info.")

    dl_response = requests.post(
        'https://spotiydownloader.com/api/download',
        json={'id': meta['id']},
        headers=headers,
        timeout=15
    )
    dl_response.raise_for_status()
    result = dl_response.json()

    if not result.get('success') or not result.get('link'):
        raise ValueError("Primary source: Failed to get download link.")

    return {
        'artist': meta.get('artists') or meta.get('artist') or 'Unknown',
        'title': meta.get('title') or 'Unknown',
        'duration': ms_to_minutes(meta['duration_ms']) if meta.get('duration_ms') else 'Unknown',
        'image': meta.get('cover'),
        'download': result['link']
    }

def spotmate_download(url):
    session = requests.Session()
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36'
    }

    visit_response = session.get('https://spotmate.online/en', headers=headers, timeout=15)
    visit_response.raise_for_status()
    cookies = visit_response.cookies.get_dict()

    soup = BeautifulSoup(visit_response.text, 'html.parser')
    csrf_token = soup.find('meta', {'name': 'csrf-token'})
    if not csrf_token:
        raise ValueError('Spotmate: CSRF token not found.')
    token = csrf_token['content']

    # Info
    info_headers = {
        **headers,
        'content-type': 'application/json',
        'cookie': "; ".join([f"{k}={v}" for k, v in cookies.items()]),
        'x-csrf-token': token,
        'origin': 'https://spotmate.online',
        'referer': 'https://spotmate.online/en',
    }

    info_response = session.post(
        'https://spotmate.online/getTrackData',
        json={'spotify_url': url},
        headers=info_headers,
        timeout=15
    )
    info_response.raise_for_status()
    info = info_response.json()

    # Convert
    convert_response = session.post(
        'https://spotmate.online/convert',
        json={'urls': url},
        headers=info_headers,
        timeout=15
    )
    convert_response.raise_for_status()
    convert = convert_response.json()

    if not convert.get('url'):
        raise ValueError('Spotmate: Failed to get download link.')

    return {
        'artist': info.get('artist') or 'Unknown',
        'title': info.get('album', {}).get('name') or 'Unknown',
        'duration': 'Unknown',  # Spotmate mein time nahi hai
        'image': None,
        'download': convert['url']
    }

@app.route('/spotify', methods=['GET'])
def spotify_route():
    url = request.args.get('url')
    if not url:
        return jsonify({'status': False, 'error': 'URL is required.'}), 400

    try:
        try:
            data = spotify_primary(url)
            return jsonify({'status': True, 'source': 'primary', 'data': data}), 200
        except Exception as primary_error:
            print(f"Primary failed: {primary_error}")
            # Fallback
            data = spotmate_download(url)
            return jsonify({'status': True, 'source': 'fallback', 'data': data}), 200

    except Exception as final_error:
        return jsonify({'status': False, 'error': f"❌ Final error: {str(final_error)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
