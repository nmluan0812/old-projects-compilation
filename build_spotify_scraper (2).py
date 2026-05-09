#!/usr/bin/env python3
"""
Build the Spotify Scraper project.

Usage:  python build_spotify_scraper.py
Output: ./spotify_scraper/

WARNING: Contains API credentials. Do NOT commit. Rotate keys if exposed.
"""

import os

OUT = "spotify_scraper"

SPOTIFY_CLIENT_ID = "11e5f27d4a954b73986e29d7ef373e14"
SPOTIFY_CLIENT_SECRET = "adac89cabf574a0bafa8b9b8f908b022"

FILES = {}

FILES["client.py"] = r'''import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def get_client():
    cid = os.environ.get("SPOTIFY_CLIENT_ID")
    secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not cid or not secret:
        raise RuntimeError("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET (in .env or environment).")
    return spotipy.Spotify(auth_manager=SpotifyClientCredentials(cid, secret))


def ms_to_min(ms):
    ms = ms or 0
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"
'''

FILES["formatters.py"] = r'''"""Build display dicts from raw Spotify API responses.

Spotify trimmed many fields from /v1/search responses in late 2024 — track
items no longer carry 'popularity', artist items lost 'followers' and
'genres'. The /v1/tracks/{id}, /v1/albums/{id}, and /v1/artists/{id} endpoints
still carry full data, so detail pages remain rich. Use .get() defensively
everywhere so missing fields show as '-' rather than crashing.
"""
from client import ms_to_min


def search_items(res, kind):
    items = []
    if kind == "track":
        for t in (res.get("tracks") or {}).get("items") or []:
            if not t:
                continue
            items.append({
                "id": t.get("id"),
                "name": t.get("name") or "-",
                "artist": ", ".join((a or {}).get("name", "") for a in t.get("artists") or []),
                "extra": (t.get("album") or {}).get("name") or "-",
                # popularity not returned in search anymore — show duration instead
                "popularity": ms_to_min(t.get("duration_ms")),
            })
    elif kind == "album":
        for a in (res.get("albums") or {}).get("items") or []:
            if not a:
                continue
            items.append({
                "id": a.get("id"),
                "name": a.get("name") or "-",
                "artist": ", ".join((ar or {}).get("name", "") for ar in a.get("artists") or []),
                "extra": a.get("release_date") or "-",
                "popularity": "",
            })
    elif kind == "artist":
        for a in (res.get("artists") or {}).get("items") or []:
            if not a:
                continue
            items.append({
                "id": a.get("id"),
                "name": a.get("name") or "-",
                "artist": "",
                # genres no longer returned in search; use ID for clarity
                "extra": a.get("id") or "-",
                "popularity": "",
            })
    return items


def track_info(t, artist):
    album = t.get("album") or {}
    images = album.get("images") or []
    artist_followers = ((artist.get("followers") or {}).get("total")) or 0
    return {
        "name": t.get("name") or "-",
        "artists": ", ".join((a or {}).get("name", "") for a in t.get("artists") or []),
        "album": album.get("name") or "-",
        "release_date": album.get("release_date") or "-",
        "duration": ms_to_min(t.get("duration_ms")),
        "popularity": t.get("popularity", "-"),
        "explicit": "Yes" if t.get("explicit") else "No",
        "track_number": t.get("track_number") or "-",
        "disc_number": t.get("disc_number") or "-",
        "preview_url": t.get("preview_url"),
        "spotify_url": (t.get("external_urls") or {}).get("spotify"),
        "isrc": (t.get("external_ids") or {}).get("isrc", "n/a"),
        "available_markets": len(t.get("available_markets") or []),
        "artist_followers": artist_followers,
        "artist_genres": ", ".join(artist.get("genres") or []) or "n/a",
        "artist_popularity": artist.get("popularity", "-"),
        "image": images[0]["url"] if images else None,
    }


def album_info(a):
    tracks = []
    total_ms = 0
    for tr in (a.get("tracks") or {}).get("items") or []:
        if not tr:
            continue
        total_ms += tr.get("duration_ms") or 0
        tracks.append({
            "number": tr.get("track_number") or "-",
            "name": tr.get("name") or "-",
            "duration": ms_to_min(tr.get("duration_ms")),
            "explicit": tr.get("explicit", False),
            "id": tr.get("id"),
        })
    images = a.get("images") or []
    return {
        "name": a.get("name") or "-",
        "artists": ", ".join((ar or {}).get("name", "") for ar in a.get("artists") or []),
        "release_date": a.get("release_date") or "-",
        "label": a.get("label") or "n/a",
        "total_tracks": a.get("total_tracks") or len(tracks),
        "popularity": a.get("popularity", "-"),
        "genres": ", ".join(a.get("genres") or []) or "n/a",
        "copyrights": "; ".join((c or {}).get("text", "") for c in a.get("copyrights") or []),
        "total_duration": ms_to_min(total_ms),
        "avg_duration": ms_to_min(total_ms // max(1, len(tracks))),
        "explicit_count": sum(1 for tr in tracks if tr["explicit"]),
        "spotify_url": (a.get("external_urls") or {}).get("spotify"),
        "image": images[0]["url"] if images else None,
        "tracks": tracks,
    }


def artist_info(a, top, albums):
    images = a.get("images") or []
    followers = ((a.get("followers") or {}).get("total")) or 0
    return {
        "name": a.get("name") or "-",
        "followers": followers,
        "popularity": a.get("popularity", "-"),
        "genres": ", ".join(a.get("genres") or []) or "n/a",
        "spotify_url": (a.get("external_urls") or {}).get("spotify"),
        "image": images[0]["url"] if images else None,
        "top_tracks": [
            {"name": t.get("name"), "id": t.get("id"), "popularity": t.get("popularity", "-")}
            for t in top or []
        ],
        "albums": [
            {"name": al.get("name"), "id": al.get("id"), "release_date": al.get("release_date") or "-"}
            for al in albums or []
        ],
    }
'''

FILES["web.py"] = r'''from flask import Flask, render_template, request
from spotipy.exceptions import SpotifyException
from client import get_client
from formatters import search_items, track_info, album_info, artist_info

app = Flask(__name__)

VALID_KINDS = {"track", "album", "artist"}


def error_page(message, code=400):
    """Render a simple error page."""
    return render_template("error.html", message=message), code


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    kind = request.args.get("type", "track")
    if kind not in VALID_KINDS:
        return error_page(f"Invalid search type: {kind!r}. Use track, album, or artist.")
    if not q:
        return render_template("index.html")
    try:
        sp = get_client()
        res = sp.search(q=q, type=kind, limit=10)
    except SpotifyException as e:
        return error_page(f"Spotify error: {e}", 502)
    except Exception as e:
        return error_page(f"Could not reach Spotify: {e}", 502)
    return render_template("results.html", items=search_items(res, kind), type=kind, query=q)


@app.route("/track/<tid>")
def track(tid):
    try:
        sp = get_client()
        t = sp.track(tid)
        artist = sp.artist(t["artists"][0]["id"]) if t.get("artists") else {}
    except SpotifyException as e:
        return error_page(f"Track not found: {e}", 404)
    except Exception as e:
        return error_page(f"Could not reach Spotify: {e}", 502)
    return render_template("track.html", t=track_info(t, artist))


@app.route("/album/<aid>")
def album(aid):
    try:
        sp = get_client()
        a = sp.album(aid)
    except SpotifyException as e:
        return error_page(f"Album not found: {e}", 404)
    except Exception as e:
        return error_page(f"Could not reach Spotify: {e}", 502)
    return render_template("album.html", a=album_info(a))


@app.route("/artist/<aid>")
def artist(aid):
    try:
        sp = get_client()
        a = sp.artist(aid)
    except SpotifyException as e:
        return error_page(f"Artist not found: {e}", 404)
    except Exception as e:
        return error_page(f"Could not reach Spotify: {e}", 502)
    # /artists/{id}/top-tracks now requires user auth (not client_credentials)
    try:
        top = (sp.artist_top_tracks(aid) or {}).get("tracks") or []
    except Exception:
        top = []
    try:
        albums = (sp.artist_albums(aid, album_type="album", limit=10) or {}).get("items") or []
    except Exception:
        albums = []
    return render_template("artist.html", a=artist_info(a, top, albums))
'''

FILES["run.py"] = r'''#!/usr/bin/env python3
"""Entry point — links modules and starts the server."""
from web import app

if __name__ == "__main__":
    app.run(debug=True, port=5002)
'''

FILES["templates/error.html"] = r'''<!DOCTYPE html>
<html>
<head>
<title>Error</title>
<style>
  body { font-family: sans-serif; padding: 20px; max-width: 800px; }
  .err { background: #fee; border: 1px solid #c66; padding: 10px; }
</style>
</head>
<body>

<a href="/">&larr; Back to search</a>
<h2>Error</h2>
<div class="err">{{ message }}</div>

</body>
</html>
'''

FILES["templates/index.html"] = r'''<!DOCTYPE html>
<html>
<head>
<title>Spotify Scraper</title>
<style>
  body { font-family: sans-serif; padding: 20px; max-width: 800px; }
</style>
</head>
<body>

<h1>Spotify Scraper</h1>
<p>Search for a track, album, or artist and view stats from the Spotify Web API.</p>

<form action="/search" method="get">
  <input type="text" name="q" placeholder="Search query" size="40" required>
  <select name="type">
    <option value="track">Track</option>
    <option value="album">Album</option>
    <option value="artist">Artist</option>
  </select>
  <button type="submit">Search</button>
</form>

</body>
</html>
'''

FILES["templates/results.html"] = r'''<!DOCTYPE html>
<html>
<head>
<title>Results - {{ query }}</title>
<style>
  body { font-family: sans-serif; padding: 20px; max-width: 800px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ccc; padding: 6px; text-align: left; }
  th { background: #eee; }
</style>
</head>
<body>

<a href="/">&larr; New search</a>
<h2>Results for "{{ query }}" ({{ type }})</h2>

{% if not items %}
<p>No results.</p>
{% else %}
<table>
<tr>
  <th>Name</th>
  {% if type != 'artist' %}<th>Artist</th>{% endif %}
  <th>{% if type == 'track' %}Album{% elif type == 'album' %}Release{% else %}ID{% endif %}</th>
  {% if type == 'track' %}<th>Length</th>{% endif %}
  <th>View</th>
</tr>
{% for it in items %}
<tr>
  <td>{{ it.name }}</td>
  {% if type != 'artist' %}<td>{{ it.artist }}</td>{% endif %}
  <td>{{ it.extra }}</td>
  {% if type == 'track' %}<td>{{ it.popularity }}</td>{% endif %}
  <td><a href="/{{ type }}/{{ it.id }}">details</a></td>
</tr>
{% endfor %}
</table>
{% endif %}

</body>
</html>
'''

FILES["templates/track.html"] = r'''<!DOCTYPE html>
<html>
<head>
<title>{{ t.name }}</title>
<style>
  body { font-family: sans-serif; padding: 20px; max-width: 800px; }
  table { border-collapse: collapse; }
  th, td { border: 1px solid #ccc; padding: 6px; text-align: left; }
  th { background: #eee; }
  img { max-width: 250px; }
</style>
</head>
<body>

<a href="javascript:history.back()">&larr; Back</a>
<h2>{{ t.name }}</h2>
{% if t.image %}<img src="{{ t.image }}">{% endif %}

<table>
<tr><th>Artists</th><td>{{ t.artists }}</td></tr>
<tr><th>Album</th><td>{{ t.album }}</td></tr>
<tr><th>Release date</th><td>{{ t.release_date }}</td></tr>
<tr><th>Duration</th><td>{{ t.duration }}</td></tr>
<tr><th>Popularity (0-100)</th><td>{{ t.popularity }}</td></tr>
<tr><th>Explicit</th><td>{{ t.explicit }}</td></tr>
<tr><th>Track number</th><td>{{ t.track_number }} (disc {{ t.disc_number }})</td></tr>
<tr><th>ISRC</th><td>{{ t.isrc }}</td></tr>
<tr><th>Available in</th><td>{{ t.available_markets }} markets</td></tr>
<tr><th>Artist followers</th><td>{{ "{:,}".format(t.artist_followers) }}</td></tr>
<tr><th>Artist genres</th><td>{{ t.artist_genres }}</td></tr>
<tr><th>Artist popularity</th><td>{{ t.artist_popularity }}</td></tr>
{% if t.preview_url %}
<tr><th>Preview</th><td><audio controls src="{{ t.preview_url }}"></audio></td></tr>
{% endif %}
{% if t.spotify_url %}
<tr><th>Spotify</th><td><a href="{{ t.spotify_url }}" target="_blank">Open in Spotify</a></td></tr>
{% endif %}
</table>

</body>
</html>
'''

FILES["templates/album.html"] = r'''<!DOCTYPE html>
<html>
<head>
<title>{{ a.name }}</title>
<style>
  body { font-family: sans-serif; padding: 20px; max-width: 800px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ccc; padding: 6px; text-align: left; }
  th { background: #eee; }
  img { max-width: 250px; }
</style>
</head>
<body>

<a href="javascript:history.back()">&larr; Back</a>
<h2>{{ a.name }}</h2>
{% if a.image %}<img src="{{ a.image }}">{% endif %}

<h3>Album info</h3>
<table>
<tr><th>Artists</th><td>{{ a.artists }}</td></tr>
<tr><th>Release date</th><td>{{ a.release_date }}</td></tr>
<tr><th>Label</th><td>{{ a.label }}</td></tr>
<tr><th>Total tracks</th><td>{{ a.total_tracks }}</td></tr>
<tr><th>Popularity (0-100)</th><td>{{ a.popularity }}</td></tr>
<tr><th>Genres</th><td>{{ a.genres }}</td></tr>
<tr><th>Total duration</th><td>{{ a.total_duration }}</td></tr>
<tr><th>Average track length</th><td>{{ a.avg_duration }}</td></tr>
<tr><th>Explicit tracks</th><td>{{ a.explicit_count }} of {{ a.total_tracks }}</td></tr>
<tr><th>Copyright</th><td>{{ a.copyrights }}</td></tr>
{% if a.spotify_url %}
<tr><th>Spotify</th><td><a href="{{ a.spotify_url }}" target="_blank">Open in Spotify</a></td></tr>
{% endif %}
</table>

<h3>Tracks</h3>
<table>
<tr><th>#</th><th>Name</th><th>Length</th><th>Explicit</th><th></th></tr>
{% for tr in a.tracks %}
<tr>
  <td>{{ tr.number }}</td>
  <td>{{ tr.name }}</td>
  <td>{{ tr.duration }}</td>
  <td>{{ 'Yes' if tr.explicit else '' }}</td>
  <td><a href="/track/{{ tr.id }}">details</a></td>
</tr>
{% endfor %}
</table>

</body>
</html>
'''

FILES["templates/artist.html"] = r'''<!DOCTYPE html>
<html>
<head>
<title>{{ a.name }}</title>
<style>
  body { font-family: sans-serif; padding: 20px; max-width: 800px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ccc; padding: 6px; text-align: left; }
  th { background: #eee; }
  img { max-width: 250px; }
</style>
</head>
<body>

<a href="javascript:history.back()">&larr; Back</a>
<h2>{{ a.name }}</h2>
{% if a.image %}<img src="{{ a.image }}">{% endif %}

<table>
<tr><th>Followers</th><td>{{ "{:,}".format(a.followers) }}</td></tr>
<tr><th>Popularity (0-100)</th><td>{{ a.popularity }}</td></tr>
<tr><th>Genres</th><td>{{ a.genres }}</td></tr>
{% if a.spotify_url %}
<tr><th>Spotify</th><td><a href="{{ a.spotify_url }}" target="_blank">Open in Spotify</a></td></tr>
{% endif %}
</table>

<h3>Top tracks</h3>
{% if a.top_tracks %}
<table>
<tr><th>Name</th><th>Popularity</th><th></th></tr>
{% for t in a.top_tracks %}
<tr><td>{{ t.name }}</td><td>{{ t.popularity }}</td><td><a href="/track/{{ t.id }}">details</a></td></tr>
{% endfor %}
</table>
{% else %}
<p style="color:#666;">Top tracks endpoint requires user-authorization (not available with client-credentials flow).</p>
{% endif %}

<h3>Albums</h3>
{% if a.albums %}
<table>
<tr><th>Name</th><th>Release date</th><th></th></tr>
{% for al in a.albums %}
<tr><td>{{ al.name }}</td><td>{{ al.release_date }}</td><td><a href="/album/{{ al.id }}">details</a></td></tr>
{% endfor %}
</table>
{% else %}
<p style="color:#666;">No albums available.</p>
{% endif %}

</body>
</html>
'''

FILES["README.md"] = r'''# Spotify Scraper

Search Spotify for tracks, albums, and artists, and view stats about them.

## Setup

```
pip install -r requirements.txt
python run.py
```

API credentials are read from the `.env` file (already created by the build script). Open http://localhost:5002 in your browser.

## Modules

| File             | Purpose                                                  |
|------------------|----------------------------------------------------------|
| `client.py`      | Loads `.env`, creates the Spotipy client, helpers        |
| `formatters.py`  | Builds display dicts from raw Spotify API responses      |
| `web.py`         | Flask app and routes                                     |
| `run.py`         | Entry point — imports `web.app` and starts the server    |

## What it shows

- **Track:** artists, album, release date, duration, popularity, explicit flag, track/disc number, ISRC, market count, artist follower count, artist genres, artist popularity, 30-second preview audio.
- **Album:** artists, release date, label, track count, popularity, genres, total/average duration, explicit track count, copyright, full track listing.
- **Artist:** follower count, popularity, genres, top 10 tracks, album list.

## Notes on Spotify API changes

Spotify has been progressively restricting the client-credentials auth flow throughout 2024-2025. Discovered constraints, all handled by this code:

- **Search `limit` is capped at 10** (was 50). The app uses `limit=10`.
- **Track results in `/v1/search`** no longer carry `popularity` — the search results page shows track length instead.
- **Artist results in `/v1/search`** no longer carry `followers` or `genres` — these may still appear on the artist detail page (which uses `/v1/artists/{id}`), but `followers` can come back as `None` even there.
- **`/v1/artists/{id}/top-tracks`** returns 403 in client-credentials mode. The artist page falls back gracefully with a note.
- **`/v1/audio-features`** and **`/v1/audio-analysis`** (danceability, energy, tempo, valence) were deprecated for new applications in late 2024 — not used.

Detail pages for tracks and albums still work fully. All formatters use `.get()` defensively so any further field removals show as `-` rather than crashing.
'''

FILES["requirements.txt"] = "flask\nspotipy\npython-dotenv\n"

FILES[".env"] = (
    f"SPOTIFY_CLIENT_ID={SPOTIFY_CLIENT_ID}\n"
    f"SPOTIFY_CLIENT_SECRET={SPOTIFY_CLIENT_SECRET}\n"
)

FILES[".gitignore"] = ".env\n__pycache__/\n*.pyc\n"


def main():
    for rel, content in FILES.items():
        path = os.path.join(OUT, rel)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print("wrote", path)
    print("\nDone.")
    print("Next:")
    print("  cd", OUT)
    print("  pip install -r requirements.txt")
    print("  python run.py")


if __name__ == "__main__":
    main()
