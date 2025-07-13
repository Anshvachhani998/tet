from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

@app.route("/artist_songs", methods=["GET"])
def get_artist_songs():
    artist_name = request.args.get("name")
    if not artist_name:
        return jsonify({"error": "Please provide artist name"}), 400

    # Step 1: Search artist
    search_url = f"https://www.jiosaavn.com/api.php?__call=search.getResults&_format=json&_marker=0&query={artist_name}&ctx=web6dot0"
    search_res = requests.get(search_url)
    search_res.raise_for_status()
    search_data = search_res.json()

    artists = search_data.get("artists", {}).get("data", [])
    if not artists:
        return jsonify({"error": "Artist not found"}), 404

    # Use first artist
    artist = artists[0]
    artist_url = artist.get("perma_url")

    # Step 2: Use artist page to get albums
    artist_page_url = f"{artist_url}"
    artist_page_html = requests.get(artist_page_url).text

    # Extract album URLs from artist page HTML using regex
    album_urls = re.findall(r'/album/[^"]+', artist_page_html)
    album_urls = list(set(album_urls))  # unique

    all_songs = []

    for album_url in album_urls:
        album_api_url = f"https://www.jiosaavn.com/api.php?__call=webapi.get&token={album_url.split('/')[-1]}&type=album&_format=json"
        album_res = requests.get(album_api_url)
        if album_res.status_code != 200:
            continue
        album_data = album_res.json()
        songs = album_data.get("songs", [])
        for song in songs:
            all_songs.append({
                "id": song.get("id"),
                "title": song.get("title"),
                "album": album_data.get("title"),
                "perma_url": song.get("perma_url")
            })

    return jsonify({
        "artist_name": artist_name,
        "total_songs": len(all_songs),
        "songs": all_songs
    })
      
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>JioSaavn Artist Song Search</title>
<style>
  body {
    font-family: Arial, sans-serif; background: #f0f0f0; padding: 20px;
  }
  .container {
    max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
  }
  input[type=text] {
    width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box;
    border: 1px solid #ccc; border-radius: 4px;
  }
  button {
    background-color: #0073e6; color: white; padding: 10px 20px;
    border: none; border-radius: 4px; cursor: pointer;
  }
  button:hover {
    background-color: #005bb5;
  }
  .song-list {
    margin-top: 20px;
  }
  .song-list li {
    margin-bottom: 8px;
  }
</style>
</head>
<body>
  <div class="container">
    <h2>Search Artist Songs on JioSaavn</h2>
    <form method="POST">
      <label for="artist">Artist Name:</label><br />
      <input type="text" id="artist" name="artist" placeholder="Enter artist name" required /><br />
      <button type="submit">Search Songs</button>
    </form>

    {% if error %}
      <p style="color:red;">{{ error }}</p>
    {% endif %}

    {% if artist_name %}
      <h3>Songs by {{ artist_name }}</h3>
      {% if songs %}
        <ul class="song-list">
          {% for song in songs %}
            <li>{{ song['name'] }}</li>
          {% endfor %}
        </ul>
      {% else %}
        <p>No songs found.</p>
      {% endif %}
    {% endif %}
  </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    artist_name = None
    songs = []
    error = None

    if request.method == "POST":
        artist_name = request.form.get("artist")
        if artist_name:
            # Step 1: Search artist to get artist id
            search_url = f"https://jiosaavn.funtoonsmultimedia.workers.dev/api/search/artists?query={artist_name}"
            try:
                resp = requests.get(search_url)
                data = resp.json()
                if data.get("success") and data["data"]["total"] > 0:
                    artist = data["data"]["results"][0]
                    artist_id = artist["id"]
                    artist_name = artist["name"]

                    # Step 2: Get songs by artist id
                    songs_url = f"https://jiosaavn.funtoonsmultimedia.workers.dev/api/artists/{artist_id}/songs"
                    songs_resp = requests.get(songs_url)
                    songs_data = songs_resp.json()
                    if songs_data.get("success") and songs_data["data"]:
                        songs = songs_data["data"]
                    else:
                        error = "No songs found for this artist."
                else:
                    error = "Artist not found."
            except Exception as e:
                error = "Error fetching data from API."

    return render_template_string(HTML_TEMPLATE, artist_name=artist_name, songs=songs, error=error)


if __name__ == "__main__":
    app.run(debug=True)
