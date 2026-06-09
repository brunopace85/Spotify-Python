import os
from flask import Flask, redirect, render_template_string, request, session, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-safe-key")

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI")
SCOPE = "user-top-read"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True,
    )

# --- HTML TEMPLATES USING TAILWIND CSS ---

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spotify Top 5</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white flex flex-col items-center justify-center min-h-screen font-sans">
    <div class="text-center p-8 bg-gray-800 rounded-2xl shadow-xl max-w-sm w-full border border-gray-700">
        <div class="text-green-500 mb-4 text-6xl flex justify-center">
            🎵
        </div>
        <h1 class="text-2xl font-bold mb-2">Spotify Stats</h1>
        <p class="text-gray-400 mb-6 text-sm">Discover your top 5 most listened tracks over the past few weeks.</p>
        <a href="/login" class="inline-block w-full bg-green-500 hover:bg-green-600 text-black font-semibold py-3 px-6 rounded-full transition duration-300 ease-in-out transform hover:scale-105 shadow-md">
            Login with Spotify
        </a>
    </div>
</body>
</html>
"""

TRACKS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Top 5 Tracks</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen py-12 px-4 font-sans">
    <div class="max-w-xl mx-auto">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-500">
                Your Top 5 Tracks
            </h1>
            <a href="/logout" class="text-xs text-gray-400 hover:text-red-400 border border-gray-700 hover:border-red-400 px-3 py-1 rounded-full transition">
                Logout
            </a>
        </div>

        <div class="space-y-4">
            {% for track in tracks %}
            <div class="flex items-center bg-gray-800 p-4 rounded-xl border border-gray-700 hover:border-green-500/50 transition-all duration-200 shadow-md group">
                <span class="text-xl font-bold text-gray-500 w-8 text-center group-hover:text-green-400 transition-colors">
                    {{ loop.index }}
                </span>
                
                <img src="{{ track.image_url }}" alt="{{ track.album_name }}" class="w-16 h-16 rounded-lg object-cover shadow-md mx-4">
                
                <div class="flex-1 min-w-0">
                    <p class="text-base font-semibold truncate text-white group-hover:text-green-400 transition-colors">
                        {{ track.name }}
                    </p>
                    <p class="text-sm text-gray-400 truncate mt-0.5">
                        {{ track.artists }}
                    </p>
                    <span class="inline-block text-[10px] bg-gray-700 text-gray-400 px-2 py-0.5 rounded mt-1 max-w-full truncate">
                        {{ track.album_name }}
                    </span>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <p class="text-center text-xs text-gray-500 mt-8 tracking-wide">Data reflects your approximate playback behavior over the last 4 weeks.</p>
    </div>
</body>
</html>
"""

# --- ROUTES ---

@app.route("/")
def index():
    token_info = session.get("token_info", None)

    if not token_info:
        return render_template_string(LOGIN_HTML)

    sp = spotipy.Spotify(auth=token_info["access_token"])

    try:
        results = sp.current_user_top_tracks(limit=5, time_range="short_term")
        
        # Parse out data structured specifically for our template
        formatted_tracks = []
        for item in results["items"]:
            # Spotify provides images array [large, medium, small]. index 1 is usually 300x300px
            image_url = item["album"]["images"][1]["url"] if len(item["album"]["images"]) > 1 else "https://via.placeholder.com/150"
            
            formatted_tracks.append({
                "name": item["name"],
                "artists": ", ".join([artist["name"] for artist in item["artists"]]),
                "album_name": item["album"]["name"],
                "image_url": image_url
            })

        return render_template_string(TRACKS_HTML, tracks=formatted_tracks)

    except Exception as e:
        print(f"Error encountered: {e}")
        return redirect(url_for("logout"))


@app.route("/login")
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route("/callback")
def callback():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=8080, host="0.0.0.0", ssl_context="adhoc")