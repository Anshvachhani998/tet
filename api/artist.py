import json
import requests

def handler(request):
    # Query param: ?name=arijit
    artist_name = request.args.get("name")
    if not artist_name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Please provide artist name as ?name=<artist_name>"})
        }

    url = f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&query={artist_name}"
    response = requests.get(url)
    if response.status_code != 200:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to fetch from JioSaavn"})
        }

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

    return {
        "statusCode": 200,
        "body": json.dumps({"artists": result}),
        "headers": {"Content-Type": "application/json"}
    }
