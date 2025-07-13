from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ✅ Root route — server health check
@app.route("/", methods=["GET"])
def home():
    return "Server is running! ✅"

# ✅ Artist route — JioSaavn artist search
@app.route("/artist", methods=["GET"])
def get_artist():
    artist_name = request.args.get("name")
    if not artist_name:
        return jsonify({"error": "Please provide artist name as ?name=<artist_name>"}), 400

    url = f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&query={artist_name}"
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch from JioSaavn"}), 500

    data = response.json()
    artists = data.get("artists", {}).get("data", [])
    result = []
    for artist in artists:
        result.append({
            "id": artist.get("id"),
            "name": artist.get("title"),
            "permalink": artist.get("perma_url"),
            "image": artist.get("image")
        })

    return jsonify({"artists": result})

@app.route("/artist_songs", methods=["GET"])
def get_artist_songs():
    artist_id = request.args.get("id")
    if not artist_id:
        return jsonify({"error": "Please provide artist ID as ?id=<artist_id>"}), 400

    url = f"https://www.jiosaavn.com/api.php?__call=artist.getArtistPageDetails&_format=json&_marker=0&artistid={artist_id}"
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch from JioSaavn"}), 500

    data = response.json()
    top_songs = data.get("topSongs", [])
    result = []
    for song in top_songs:
        result.append({
            "id": song.get("id"),
            "title": song.get("title"),
            "permalink": song.get("perma_url"),
            "image": song.get("image"),
            "album": song.get("album"),
            "primary_artists": song.get("more_info", {}).get("primary_artists")
        })

    return jsonify({"top_songs": result})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
