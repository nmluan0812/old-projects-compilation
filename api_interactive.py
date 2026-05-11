#!/usr/bin/env python3
"""
Build the API Interactive project.

Usage:  python build_api_interactive.py
Output: ./api_interactive/

"""

import os

OUT = "api_interactive"

SPOTIFY_CLIENT_ID = "11e5f27d4a954b73986e29d7ef373e14"
SPOTIFY_CLIENT_SECRET = "adac89cabf574a0bafa8b9b8f908b022"
YOUTUBE_API_KEY = "AIzaSyD8NJu40RRjbpuh3uxxfg6t_H8cnuNrpoE"

FILES = {}

FILES["http_util.py"] = r'''import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests


def safe_get(url, params=None, headers=None):
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        try:
            return {"status": r.status_code, "data": r.json()}
        except ValueError:
            return {"status": r.status_code, "data": r.text}
    except Exception as e:
        return {"status": 0, "data": {"error": str(e)}}
'''

FILES["services.py"] = r'''import os
import requests
from http_util import safe_get


# ---------- Auth-required ----------

def spotify_token():
    cid = os.environ.get("SPOTIFY_CLIENT_ID")
    secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not cid or not secret:
        return None
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(cid, secret),
        timeout=10,
    )
    return r.json().get("access_token")


def spotify_search(query, kind):
    token = spotify_token()
    if not token:
        return {"status": 0, "data": {"error": "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET."}}
    return safe_get(
        "https://api.spotify.com/v1/search",
        params={"q": query, "type": kind, "limit": 5},
        headers={"Authorization": f"Bearer {token}"},
    )


def youtube_search(query):
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        return {"status": 0, "data": {"error": "Set YOUTUBE_API_KEY."}}
    return safe_get(
        "https://www.googleapis.com/youtube/v3/search",
        params={"part": "snippet", "q": query, "maxResults": 5, "key": key},
    )


# ---------- Lookups ----------

def wikipedia(title):
    if not title:
        return {"status": 0, "data": {"error": "Provide a title"}}
    safe_title = title.strip().replace(" ", "_")
    return safe_get(
        f"https://en.wikipedia.org/api/rest_v1/page/summary/{safe_title}",
        headers={"User-Agent": "api-interactive/1.0 (educational)"},
    )


def dictionary(word):
    return safe_get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")


def tv_shows(query):
    return safe_get("https://api.tvmaze.com/search/shows", params={"q": query})


def books(query):
    return safe_get("https://openlibrary.org/search.json", params={"q": query, "limit": 10})


def country_name(name):
    return safe_get(f"https://restcountries.com/v3.1/name/{name}")


def country_code(code):
    return safe_get(f"https://restcountries.com/v3.1/alpha/{code}")


def holidays(year, country):
    y = year or "2026"
    c = (country or "US").upper()
    return safe_get(f"https://date.nager.at/api/v3/PublicHolidays/{y}/{c}")


def pokemon(name):
    return safe_get(f"https://pokeapi.co/api/v2/pokemon/{name.lower()}")


# ---------- Profiles ----------

def github_user(username):
    return safe_get(f"https://api.github.com/users/{username}")


def github_repos(username):
    return safe_get(
        f"https://api.github.com/users/{username}/repos",
        params={"sort": "updated", "per_page": 10},
    )


def ip_info(ip):
    url = f"https://ipapi.co/{ip}/json/" if ip else "https://ipapi.co/json/"
    return safe_get(url)


# ---------- Roblox ----------

def roblox_user(username):
    try:
        r = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            json={"usernames": [username], "excludeBannedUsers": False},
            timeout=10,
        )
        users = r.json().get("data", [])
        if not users:
            return {"status": r.status_code, "data": {"error": "User not found"}}
        info = requests.get(f"https://users.roblox.com/v1/users/{users[0]['id']}", timeout=10).json()
        return {"status": 200, "data": info}
    except Exception as e:
        return {"status": 0, "data": {"error": str(e)}}


def roblox_user_by_id(user_id):
    return safe_get(f"https://users.roblox.com/v1/users/{user_id}")


def roblox_group(group_id):
    return safe_get(f"https://groups.roblox.com/v1/groups/{group_id}")


def roblox_user_groups(user_id):
    return safe_get(f"https://groups.roblox.com/v2/users/{user_id}/groups/roles")


def roblox_social(user_id):
    base = f"https://friends.roblox.com/v1/users/{user_id}"
    try:
        f = requests.get(f"{base}/friends/count", timeout=5).json().get("count")
        a = requests.get(f"{base}/followers/count", timeout=5).json().get("count")
        b = requests.get(f"{base}/followings/count", timeout=5).json().get("count")
        return {"status": 200, "data": {"friends": f, "followers": a, "following": b}}
    except Exception as e:
        return {"status": 0, "data": {"error": str(e)}}


def roblox_game(place_id):
    if not place_id:
        return {"status": 0, "data": {"error": "Provide a place ID"}}
    try:
        r1 = requests.get(
            f"https://apis.roblox.com/universes/v1/places/{place_id}/universe",
            timeout=10,
        )
        if r1.status_code != 200:
            return {"status": r1.status_code, "data": {"error": "Could not resolve universe"}}
        universe_id = r1.json().get("universeId")
        if not universe_id:
            return {"status": 404, "data": {"error": "No universe for that place ID"}}
        return safe_get("https://games.roblox.com/v1/games", params={"universeIds": universe_id})
    except Exception as e:
        return {"status": 0, "data": {"error": str(e)}}


# ---------- Entertainment (NEW) ----------

def recipes(query):
    return safe_get("https://www.themealdb.com/api/json/v1/1/search.php", params={"s": query})


def cocktails(query):
    return safe_get("https://www.thecocktaildb.com/api/json/v1/1/search.php", params={"s": query})


def anime(query):
    return safe_get("https://api.jikan.moe/v4/anime", params={"q": query, "limit": 5})


def star_wars(query):
    """SWAPI returns a flat array; filter client-side by name."""
    res = safe_get("https://swapi.info/api/people/")
    if res.get("status") != 200 or not isinstance(res.get("data"), list):
        return res
    if query:
        ql = query.lower()
        filtered = [p for p in res["data"] if ql in (p.get("name") or "").lower()]
    else:
        filtered = res["data"][:10]
    return {"status": 200, "data": filtered[:10]}


def dnd_spell(name):
    if not name:
        return {"status": 0, "data": {"error": "Provide a spell name"}}
    slug = name.lower().strip().replace(" ", "-").replace("'", "")
    return safe_get(f"https://www.dnd5eapi.co/api/2014/spells/{slug}")


# ---------- Live data ----------

def weather(lat, lon):
    return safe_get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "current_weather": "true"},
    )


def geocode(name):
    return safe_get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": name, "count": 5},
    )


def crypto(ids):
    return safe_get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": ids or "bitcoin,ethereum", "vs_currencies": "usd"},
    )


def exchange(base, to):
    return safe_get(
        "https://api.frankfurter.app/latest",
        params={"from": base or "USD", "to": to or "EUR,GBP,JPY"},
    )


def nasa_apod(api_key):
    return safe_get(
        "https://api.nasa.gov/planetary/apod",
        params={"api_key": api_key or "DEMO_KEY"},
    )


def sun_times(lat, lon):
    return safe_get(
        "https://api.sunrise-sunset.org/json",
        params={"lat": lat, "lng": lon, "formatted": "0"},
    )


def world_time(timezone):
    return safe_get(
        "https://timeapi.io/api/Time/current/zone",
        params={"timeZone": timezone or "UTC"},
    )


# ---------- News & Social ----------

def reddit_top(subreddit):
    return safe_get(
        f"https://www.reddit.com/r/{subreddit}/top.json",
        params={"limit": 10, "t": "day"},
        headers={"User-Agent": "api-interactive/1.0"},
    )


def hacker_news(count):
    try:
        n = max(1, min(int(count or "10"), 30))
        ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()
        stories = []
        for sid in ids[:n]:
            try:
                stories.append(
                    requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=5).json()
                )
            except Exception:
                pass
        return {"status": 200, "data": {"stories": stories}}
    except Exception as e:
        return {"status": 0, "data": {"error": str(e)}}


# ---------- Random / fun ----------

def joke():
    return safe_get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"})


def joke_api(category, joke_type):
    cat = category or "Any"
    params = {"blacklistFlags": "nsfw,religious,political,racist,sexist,explicit"}
    if joke_type and joke_type != "any":
        params["type"] = joke_type
    return safe_get(f"https://v2.jokeapi.dev/joke/{cat}", params=params)


def cat_fact():
    return safe_get("https://catfact.ninja/fact")


def random_fact():
    """Replaces numbers_fact (numbersapi.com is dead)."""
    return safe_get("https://uselessfacts.jsph.pl/api/v2/facts/random")


def advice():
    return safe_get("https://api.adviceslip.com/advice")


def trivia(amount):
    return safe_get("https://opentdb.com/api.php", params={"amount": amount or "5"})


def random_user():
    return safe_get("https://randomuser.me/api/")


def agify(name):
    return safe_get("https://api.agify.io/", params={"name": name})


def genderize(name):
    return safe_get("https://api.genderize.io/", params={"name": name})


def quote():
    return safe_get("https://zenquotes.io/api/random")
'''

FILES["formatters.py"] = r'''"""Each formatter takes raw API data + caller params and returns one of:
    {"type": "text",   "text": str}
    {"type": "fields", "fields": [{"label": str, "value": str}, ...]}
    {"type": "table",  "headers": [str, ...], "rows": [[..], ..]}
    {"type": "error",  "message": str}

Formatters use .get() with defaults everywhere — APIs change shape, and a
missing optional field should not crash the response.
"""
import html


def _f(label, value):
    return {"label": label, "value": "-" if value is None or value == "" else str(value)}


def _text(s):
    return {"type": "text", "text": str(s) if s is not None else "-"}


def _fields(items):
    return {"type": "fields", "fields": items}


def _table(headers, rows):
    return {"type": "table", "headers": list(headers), "rows": [list(r) for r in rows]}


def _ms_to_min(ms):
    ms = ms or 0
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"


# ---------- Search ----------

def f_spotify_search(data, params):
    """Spotify trimmed many fields from /v1/search in late 2024:
    - track items no longer include 'popularity'
    - artist items no longer include 'followers' or 'genres'
    - playlist items can be null
    Be defensive throughout.
    """
    kind = params.get("type", "track")

    if kind == "track":
        rows = []
        for t in (data.get("tracks") or {}).get("items") or []:
            if not t:
                continue
            artists = ", ".join((a or {}).get("name", "") for a in t.get("artists") or [])
            album = (t.get("album") or {}).get("name") or "-"
            duration = _ms_to_min(t.get("duration_ms"))
            explicit = "Yes" if t.get("explicit") else ""
            rows.append([t.get("name"), artists, album, duration, explicit])
        return _table(["Name", "Artist", "Album", "Duration", "Explicit"], rows)

    if kind == "album":
        rows = []
        for a in (data.get("albums") or {}).get("items") or []:
            if not a:
                continue
            artists = ", ".join((ar or {}).get("name", "") for ar in a.get("artists") or [])
            rows.append([a.get("name"), artists, a.get("release_date"), a.get("total_tracks")])
        return _table(["Name", "Artist", "Release", "Tracks"], rows)

    if kind == "artist":
        rows = []
        for a in (data.get("artists") or {}).get("items") or []:
            if not a:
                continue
            url = (a.get("external_urls") or {}).get("spotify", "")
            rows.append([a.get("name"), a.get("id"), url])
        return _table(["Name", "ID", "Spotify URL"], rows)

    if kind == "playlist":
        rows = []
        for p in (data.get("playlists") or {}).get("items") or []:
            if not p:
                continue
            owner = (p.get("owner") or {}).get("display_name") or "-"
            desc = (p.get("description") or "")[:80]
            url = (p.get("external_urls") or {}).get("spotify", "")
            rows.append([p.get("name"), owner, desc, url])
        return _table(["Name", "Owner", "Description", "URL"], rows)

    return _text("Unknown search type")


def f_youtube_search(data, params):
    rows = []
    for item in data.get("items") or []:
        s = item.get("snippet") or {}
        rows.append([s.get("title", ""), s.get("channelTitle", ""), (s.get("publishedAt") or "")[:10]])
    return _table(["Title", "Channel", "Published"], rows)


# ---------- Lookups ----------

def f_wikipedia(data, params):
    url = ((data.get("content_urls") or {}).get("desktop") or {}).get("page", "")
    return _fields([
        _f("Title", data.get("title")),
        _f("Description", data.get("description")),
        _f("Extract", data.get("extract")),
        _f("URL", url),
    ])


def f_dictionary(data, params):
    if not isinstance(data, list) or not data:
        return {"type": "error", "message": "No definitions found"}
    entry = data[0]
    fields = [
        _f("Word", entry.get("word")),
        _f("Phonetic", entry.get("phonetic", "-")),
    ]
    for m in (entry.get("meanings") or [])[:5]:
        pos = m.get("partOfSpeech", "")
        defs = "; ".join((d or {}).get("definition", "") for d in (m.get("definitions") or [])[:2])
        fields.append(_f(pos or "definition", defs))
    return _fields(fields)


def f_tv_shows(data, params):
    rows = []
    for item in data or []:
        s = item.get("show") or {}
        net_obj = s.get("network") or s.get("webChannel") or {}
        net = net_obj.get("name") if net_obj else "-"
        genres = ", ".join(s.get("genres") or [])
        rows.append([
            s.get("name"),
            (s.get("premiered") or "")[:4],
            s.get("status"),
            net or "-",
            genres or "-",
            (s.get("rating") or {}).get("average") or "-",
        ])
    return _table(["Name", "Year", "Status", "Network", "Genres", "Rating"], rows)


def f_books(data, params):
    rows = []
    for d in (data.get("docs") or [])[:10]:
        authors = ", ".join((d.get("author_name") or [])[:2])
        lang = (d.get("language") or ["?"])[0]
        rows.append([d.get("title"), authors or "-", d.get("first_publish_year"), lang])
    return _table(["Title", "Authors", "First published", "Language"], rows)


def _country_row(c):
    cap = ((c.get("capital") or ["-"])[0]) if c.get("capital") else "-"
    langs = ", ".join((c.get("languages") or {}).values())
    return [(c.get("name") or {}).get("common"), cap, c.get("region"), c.get("population"), langs]


def f_country_name(data, params):
    if not isinstance(data, list):
        return {"type": "error", "message": "No country found"}
    return _table(["Name", "Capital", "Region", "Population", "Languages"],
                  [_country_row(c) for c in data[:10]])


def f_country_code(data, params):
    if not isinstance(data, list) or not data:
        return {"type": "error", "message": "No country found"}
    c = data[0]
    return _fields([
        _f("Name", (c.get("name") or {}).get("common")),
        _f("Official name", (c.get("name") or {}).get("official")),
        _f("Capital", (c.get("capital") or ["-"])[0] if c.get("capital") else "-"),
        _f("Region", c.get("region")),
        _f("Subregion", c.get("subregion")),
        _f("Population", c.get("population")),
        _f("Area (km²)", c.get("area")),
        _f("Languages", ", ".join((c.get("languages") or {}).values())),
        _f("Currencies", ", ".join((c.get("currencies") or {}).keys())),
        _f("Timezones", ", ".join(c.get("timezones") or [])),
    ])


def f_holidays(data, params):
    if not isinstance(data, list):
        return {"type": "error", "message": "Bad response"}
    return _table(["Date", "Local Name", "English Name"],
                  [[h.get("date"), h.get("localName"), h.get("name")] for h in data])


def f_pokemon(data, params):
    types = ", ".join((t.get("type") or {}).get("name", "") for t in data.get("types") or [])
    abilities = ", ".join((a.get("ability") or {}).get("name", "") for a in data.get("abilities") or [])
    stats = "; ".join(f"{(s.get('stat') or {}).get('name','')} {s.get('base_stat','')}" for s in data.get("stats") or [])
    return _fields([
        _f("Name", data.get("name")),
        _f("ID", data.get("id")),
        _f("Types", types),
        _f("Abilities", abilities),
        _f("Height (dm)", data.get("height")),
        _f("Weight (hg)", data.get("weight")),
        _f("Base experience", data.get("base_experience")),
        _f("Stats", stats),
    ])


# ---------- Profiles ----------

def f_github_user(data, params):
    return _fields([
        _f("Login", data.get("login")),
        _f("Name", data.get("name")),
        _f("Bio", data.get("bio")),
        _f("Company", data.get("company")),
        _f("Location", data.get("location")),
        _f("Public repos", data.get("public_repos")),
        _f("Followers", data.get("followers")),
        _f("Following", data.get("following")),
        _f("Created", (data.get("created_at") or "")[:10]),
    ])


def f_github_repos(data, params):
    rows = [[r.get("name"), r.get("stargazers_count"), r.get("language") or "-",
             (r.get("description") or "")[:80]] for r in data or []]
    return _table(["Name", "Stars", "Language", "Description"], rows)


def f_ip_info(data, params):
    return _fields([
        _f("IP", data.get("ip")),
        _f("City", data.get("city")),
        _f("Region", data.get("region")),
        _f("Country", data.get("country_name")),
        _f("Postal", data.get("postal")),
        _f("ISP / Org", data.get("org")),
        _f("Timezone", data.get("timezone")),
        _f("Lat / Lon", f"{data.get('latitude')}, {data.get('longitude')}"),
    ])


# ---------- Roblox ----------

def f_roblox_user(data, params):
    return _fields([
        _f("Name", data.get("name")),
        _f("Display name", data.get("displayName")),
        _f("ID", data.get("id")),
        _f("Created", (data.get("created") or "")[:10]),
        _f("Banned", data.get("isBanned")),
        _f("Description", data.get("description") or "-"),
    ])


def f_roblox_group(data, params):
    owner = data.get("owner") or {}
    return _fields([
        _f("Name", data.get("name")),
        _f("ID", data.get("id")),
        _f("Owner", owner.get("username") or "-"),
        _f("Members", data.get("memberCount")),
        _f("Public entry", data.get("publicEntryAllowed")),
        _f("Description", (data.get("description") or "-")[:300]),
    ])


def f_roblox_user_groups(data, params):
    rows = []
    for entry in data.get("data") or []:
        g = entry.get("group") or {}
        role = entry.get("role") or {}
        rows.append([g.get("name"), g.get("id"), role.get("name"), g.get("memberCount")])
    return _table(["Group", "ID", "Role", "Members"], rows)


def f_roblox_social(data, params):
    return _fields([
        _f("Friends", data.get("friends")),
        _f("Followers", data.get("followers")),
        _f("Following", data.get("following")),
    ])


def f_roblox_game(data, params):
    games = data.get("data") or []
    if not games:
        return {"type": "error", "message": "No game found"}
    g = games[0]
    return _fields([
        _f("Name", g.get("name")),
        _f("Description", (g.get("description") or "-")[:300]),
        _f("Creator", (g.get("creator") or {}).get("name")),
        _f("Playing now", g.get("playing")),
        _f("Total visits", g.get("visits")),
        _f("Max players", g.get("maxPlayers")),
        _f("Created", (g.get("created") or "")[:10]),
        _f("Updated", (g.get("updated") or "")[:10]),
    ])


# ---------- Entertainment ----------

def _mealdb_ingredients(item):
    parts = []
    for i in range(1, 21):
        ing = (item.get(f"strIngredient{i}") or "").strip()
        meas = (item.get(f"strMeasure{i}") or "").strip()
        if ing:
            parts.append((f"{meas} {ing}").strip())
    return parts


def f_recipes(data, params):
    meals = data.get("meals") or []
    if not meals:
        return {"type": "error", "message": "No recipes found"}
    rows = []
    for m in meals[:5]:
        ings = _mealdb_ingredients(m)
        rows.append([
            m.get("strMeal"),
            m.get("strCategory"),
            m.get("strArea"),
            ", ".join(ings),
        ])
    return _table(["Name", "Category", "Cuisine", "Ingredients"], rows)


def f_cocktails(data, params):
    drinks = data.get("drinks") or []
    if not drinks:
        return {"type": "error", "message": "No cocktails found"}
    rows = []
    for d in drinks[:5]:
        ings = _mealdb_ingredients(d)
        rows.append([
            d.get("strDrink"),
            d.get("strCategory"),
            d.get("strAlcoholic"),
            d.get("strGlass"),
            ", ".join(ings),
        ])
    return _table(["Name", "Category", "Alcoholic", "Glass", "Ingredients"], rows)


def f_anime(data, params):
    rows = []
    for a in data.get("data") or []:
        genres = ", ".join((g or {}).get("name", "") for g in a.get("genres") or [])
        rows.append([
            a.get("title_english") or a.get("title"),
            a.get("type"),
            a.get("episodes"),
            a.get("score"),
            a.get("year"),
            genres,
        ])
    return _table(["Title", "Type", "Episodes", "Score", "Year", "Genres"], rows)


def f_star_wars(data, params):
    if not isinstance(data, list):
        return {"type": "error", "message": "Bad response"}
    if not data:
        return {"type": "error", "message": "No characters found"}
    rows = []
    for p in data[:10]:
        rows.append([
            p.get("name"),
            p.get("birth_year"),
            p.get("gender"),
            p.get("height"),
            p.get("mass"),
            p.get("hair_color"),
        ])
    return _table(["Name", "Birth Year", "Gender", "Height", "Mass", "Hair"], rows)


def f_dnd_spell(data, params):
    classes = ", ".join((c or {}).get("name", "") for c in data.get("classes") or [])
    desc = " ".join(data.get("desc") or [])[:500]
    return _fields([
        _f("Name", data.get("name")),
        _f("Level", data.get("level")),
        _f("School", (data.get("school") or {}).get("name")),
        _f("Casting time", data.get("casting_time")),
        _f("Range", data.get("range")),
        _f("Duration", data.get("duration")),
        _f("Components", ", ".join(data.get("components") or [])),
        _f("Classes", classes),
        _f("Description", desc),
    ])


# ---------- Live data ----------

def f_weather(data, params):
    cw = data.get("current_weather") or {}
    return _fields([
        _f("Temperature (°C)", cw.get("temperature")),
        _f("Wind speed (km/h)", cw.get("windspeed")),
        _f("Wind direction (°)", cw.get("winddirection")),
        _f("Time", cw.get("time")),
    ])


def f_geocode(data, params):
    rows = [[r.get("name"), r.get("country"), r.get("admin1") or "-",
             r.get("latitude"), r.get("longitude")] for r in data.get("results") or []]
    return _table(["Name", "Country", "Region", "Lat", "Lon"], rows)


def f_crypto(data, params):
    if not isinstance(data, dict):
        return {"type": "error", "message": "Bad response"}
    rows = [[coin, "$" + str((prices or {}).get("usd", "-"))] for coin, prices in data.items()]
    return _table(["Coin", "USD"], rows)


def f_exchange(data, params):
    base = data.get("base", "")
    rows = [[k, v] for k, v in (data.get("rates") or {}).items()]
    return _table([f"Currency (1 {base} =)", "Rate"], rows)


def f_nasa_apod(data, params):
    return _fields([
        _f("Title", data.get("title")),
        _f("Date", data.get("date")),
        _f("Type", data.get("media_type")),
        _f("URL", data.get("url")),
        _f("Explanation", data.get("explanation")),
    ])


def f_sun_times(data, params):
    r = data.get("results") or {}
    return _fields([
        _f("Sunrise (UTC)", r.get("sunrise")),
        _f("Sunset (UTC)", r.get("sunset")),
        _f("Solar noon (UTC)", r.get("solar_noon")),
        _f("Day length", r.get("day_length")),
        _f("Civil twilight begin", r.get("civil_twilight_begin")),
        _f("Civil twilight end", r.get("civil_twilight_end")),
    ])


def f_world_time(data, params):
    return _fields([
        _f("Date", data.get("date")),
        _f("Time", data.get("time")),
        _f("Day of week", data.get("dayOfWeek")),
        _f("Timezone", data.get("timeZone")),
        _f("DST active", data.get("dstActive")),
    ])


# ---------- News & Social ----------

def f_reddit(data, params):
    posts = (data.get("data") or {}).get("children") or []
    rows = []
    for p in posts:
        d = p.get("data") or {}
        title = (d.get("title") or "")[:100]
        rows.append([title, d.get("author"), d.get("score"), d.get("num_comments")])
    return _table(["Title", "Author", "Score", "Comments"], rows)


def f_hacker_news(data, params):
    rows = []
    for s in data.get("stories") or []:
        if not s:
            continue
        rows.append([
            (s.get("title") or "")[:80],
            s.get("by"),
            s.get("score"),
            s.get("descendants", 0),
            s.get("url") or "(self)",
        ])
    return _table(["Title", "Author", "Score", "Comments", "URL"], rows)


# ---------- Random / fun ----------

def f_joke(data, params):
    return _text(data.get("joke") if isinstance(data, dict) else data)


def f_joke_api(data, params):
    if data.get("type") == "twopart":
        return _text(f"{data.get('setup', '')}\n\n{data.get('delivery', '')}")
    return _text(data.get("joke", "?"))


def f_cat_fact(data, params):
    return _text(data.get("fact") if isinstance(data, dict) else data)


def f_random_fact(data, params):
    return _text(data.get("text") if isinstance(data, dict) else data)


def f_advice(data, params):
    return _text((data.get("slip") or {}).get("advice"))


def f_trivia(data, params):
    rows = []
    for q in data.get("results") or []:
        rows.append([
            html.unescape(q.get("category", "")),
            q.get("difficulty", ""),
            html.unescape(q.get("question", "")),
            html.unescape(q.get("correct_answer", "")),
        ])
    return _table(["Category", "Difficulty", "Question", "Answer"], rows)


def f_random_user(data, params):
    results = data.get("results") or []
    if not results:
        return {"type": "error", "message": "No user returned"}
    u = results[0]
    n = u.get("name") or {}
    name = f"{n.get('title', '')} {n.get('first', '')} {n.get('last', '')}".strip()
    loc = u.get("location") or {}
    street = loc.get("street") or {}
    addr = f"{street.get('number', '')} {street.get('name', '')}, {loc.get('city', '')}, {loc.get('country', '')}"
    return _fields([
        _f("Name", name),
        _f("Email", u.get("email")),
        _f("Phone", u.get("phone")),
        _f("Gender", u.get("gender")),
        _f("Age", (u.get("dob") or {}).get("age")),
        _f("Nationality", u.get("nat")),
        _f("Address", addr.strip(", ")),
        _f("Username", (u.get("login") or {}).get("username")),
    ])


def f_agify(data, params):
    return _fields([
        _f("Name", data.get("name")),
        _f("Predicted age", data.get("age")),
        _f("Sample size", data.get("count")),
    ])


def f_genderize(data, params):
    return _fields([
        _f("Name", data.get("name")),
        _f("Gender", data.get("gender")),
        _f("Probability", data.get("probability")),
        _f("Sample size", data.get("count")),
    ])


def f_quote(data, params):
    if not isinstance(data, list) or not data:
        return {"type": "error", "message": "No quote returned"}
    q = data[0]
    return _fields([
        _f("Quote", q.get("q")),
        _f("Author", q.get("a")),
    ])
'''

FILES["web.py"] = r'''from flask import Flask, render_template, request, jsonify
import services
import formatters

app = Flask(__name__)

# Block name -> (service_func, formatter_func, ordered_param_names)
HANDLERS = {
    # Search
    "spotify_search": (services.spotify_search, formatters.f_spotify_search, ["query", "type"]),
    "youtube_search": (services.youtube_search, formatters.f_youtube_search, ["query"]),

    # Lookups
    "wikipedia":    (services.wikipedia,    formatters.f_wikipedia,    ["title"]),
    "dictionary":   (services.dictionary,   formatters.f_dictionary,   ["word"]),
    "tv_shows":     (services.tv_shows,     formatters.f_tv_shows,     ["query"]),
    "books":        (services.books,        formatters.f_books,        ["query"]),
    "country_name": (services.country_name, formatters.f_country_name, ["name"]),
    "country_code": (services.country_code, formatters.f_country_code, ["code"]),
    "holidays":     (services.holidays,     formatters.f_holidays,     ["year", "country"]),
    "pokemon":      (services.pokemon,      formatters.f_pokemon,      ["name"]),

    # Profiles
    "github_user":  (services.github_user,  formatters.f_github_user,  ["username"]),
    "github_repos": (services.github_repos, formatters.f_github_repos, ["username"]),
    "ip_info":      (services.ip_info,      formatters.f_ip_info,      ["ip"]),

    # Roblox
    "roblox_user":        (services.roblox_user,        formatters.f_roblox_user,        ["username"]),
    "roblox_user_by_id":  (services.roblox_user_by_id,  formatters.f_roblox_user,        ["user_id"]),
    "roblox_group":       (services.roblox_group,       formatters.f_roblox_group,       ["group_id"]),
    "roblox_user_groups": (services.roblox_user_groups, formatters.f_roblox_user_groups, ["user_id"]),
    "roblox_social":      (services.roblox_social,      formatters.f_roblox_social,      ["user_id"]),
    "roblox_game":        (services.roblox_game,        formatters.f_roblox_game,        ["place_id"]),

    # Entertainment
    "recipes":   (services.recipes,   formatters.f_recipes,   ["query"]),
    "cocktails": (services.cocktails, formatters.f_cocktails, ["query"]),
    "anime":     (services.anime,     formatters.f_anime,     ["query"]),
    "star_wars": (services.star_wars, formatters.f_star_wars, ["query"]),
    "dnd_spell": (services.dnd_spell, formatters.f_dnd_spell, ["name"]),

    # Live data
    "weather":     (services.weather,     formatters.f_weather,     ["lat", "lon"]),
    "geocode":     (services.geocode,     formatters.f_geocode,     ["name"]),
    "crypto":      (services.crypto,      formatters.f_crypto,      ["ids"]),
    "exchange":    (services.exchange,    formatters.f_exchange,    ["base", "to"]),
    "nasa_apod":   (services.nasa_apod,   formatters.f_nasa_apod,   ["api_key"]),
    "sun_times":   (services.sun_times,   formatters.f_sun_times,   ["lat", "lon"]),
    "world_time":  (services.world_time,  formatters.f_world_time,  ["timezone"]),

    # News & social
    "reddit_top":  (services.reddit_top,  formatters.f_reddit,      ["subreddit"]),
    "hacker_news": (services.hacker_news, formatters.f_hacker_news, ["count"]),

    # Random / fun
    "joke":         (services.joke,         formatters.f_joke,         []),
    "joke_api":     (services.joke_api,     formatters.f_joke_api,     ["category", "type"]),
    "cat_fact":     (services.cat_fact,     formatters.f_cat_fact,     []),
    "random_fact":  (services.random_fact,  formatters.f_random_fact,  []),
    "advice":       (services.advice,       formatters.f_advice,       []),
    "trivia":       (services.trivia,       formatters.f_trivia,       ["amount"]),
    "random_user":  (services.random_user,  formatters.f_random_user,  []),
    "agify":        (services.agify,        formatters.f_agify,        ["name"]),
    "genderize":    (services.genderize,    formatters.f_genderize,    ["name"]),
    "quote":        (services.quote,        formatters.f_quote,        []),
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/<name>", methods=["POST"])
def call_api(name):
    if name not in HANDLERS:
        return jsonify({"status": 404, "data": {"error": "Unknown API"},
                        "formatted": {"type": "error", "message": "Unknown API"}})
    service, formatter, params = HANDLERS[name]
    body = request.get_json(silent=True) or {}
    args = [body.get(p, "") for p in params]
    raw = service(*args)
    formatted = build_formatted(formatter, raw, body)
    return jsonify({"status": raw["status"], "data": raw["data"], "formatted": formatted})


def build_formatted(formatter, raw, body):
    status = raw["status"]
    bad_status = status == 0 or status < 200 or status >= 300
    # Some APIs (e.g. JokeAPI) return {"error": false} on success — check truthiness
    bad_dict = isinstance(raw["data"], dict) and bool(raw["data"].get("error"))
    if bad_status or bad_dict:
        if isinstance(raw["data"], dict):
            err = raw["data"].get("error") or raw["data"].get("message") or "Error"
            msg = err if isinstance(err, str) else str(err)
        else:
            msg = "Error"
        return {"type": "error", "message": f"HTTP {status}: {msg}"}
    try:
        return formatter(raw["data"], body)
    except Exception as e:
        return {"type": "error", "message": f"Could not format: {e}"}
'''

FILES["run.py"] = r'''#!/usr/bin/env python3
"""Entry point — links modules and starts the server."""
from web import app

if __name__ == "__main__":
    app.run(debug=True, port=5003)
'''

FILES["templates/index.html"] = r'''<!DOCTYPE html>
<html>
<head>
<title>API Interactive</title>
<style>
  body { font-family: sans-serif; margin: 0; padding: 0; }
  #wrap { display: flex; height: 100vh; }
  #palette { width: 260px; background: #eee; border-right: 1px solid #999; padding: 10px; overflow-y: auto; }
  #palette h3 { margin: 14px 0 4px 0; font-size: 12px; text-transform: uppercase; color: #555; }
  #canvas { flex: 1; padding: 10px; overflow-y: auto; background: #fafafa; }
  .block-template {
    border: 1px solid #888; background: white; padding: 6px 8px; margin-bottom: 4px;
    cursor: grab; user-select: none; font-size: 13px;
  }
  .block-template:active { cursor: grabbing; }
  .dropzone { min-height: 100%; border: 2px dashed #bbb; padding: 10px; }
  .dropzone.over { background: #e8f0ff; }
  .block { border: 1px solid #666; background: white; padding: 10px; margin-bottom: 10px; }
  .block h3 { margin: 0 0 8px 0; font-size: 14px; }
  .block label { display: inline-block; min-width: 80px; }
  .block input, .block select { margin: 2px; }
  .controls { margin-top: 8px; }
  button.run { margin-right: 6px; }
  .small { font-size: 11px; color: #666; }
  .output { margin-top: 8px; max-height: 360px; overflow: auto; border: 1px solid #ccc; padding: 6px; background: white; }
  .output.raw { background: #1e1e1e; color: #ddd; font-family: monospace; font-size: 12px; white-space: pre-wrap; }
  .output table { border-collapse: collapse; font-size: 13px; }
  .output th, .output td {
    border: 1px solid #999; padding: 4px 8px; text-align: left; vertical-align: top;
    max-width: 360px; word-wrap: break-word;
  }
  .output th { background: #ddd; }
  .err { color: #b00; }
  h2 { margin-top: 0; }
</style>
</head>
<body>

<div id="wrap">

<div id="palette">
  <h2>API Blocks</h2>
  <p class="small">Drag onto canvas, fill in fields, click Run. Toggle Display to see raw JSON.</p>

  <h3>Search</h3>
  <div class="block-template" draggable="true" data-type="spotify_search">Spotify Search</div>
  <div class="block-template" draggable="true" data-type="youtube_search">YouTube Search</div>

  <h3>Lookups</h3>
  <div class="block-template" draggable="true" data-type="wikipedia">Wikipedia</div>
  <div class="block-template" draggable="true" data-type="dictionary">Dictionary</div>
  <div class="block-template" draggable="true" data-type="tv_shows">TV Shows (TVMaze)</div>
  <div class="block-template" draggable="true" data-type="books">Books (Open Library)</div>
  <div class="block-template" draggable="true" data-type="country_name">Country by Name</div>
  <div class="block-template" draggable="true" data-type="country_code">Country by Code</div>
  <div class="block-template" draggable="true" data-type="holidays">Public Holidays</div>
  <div class="block-template" draggable="true" data-type="pokemon">Pokemon</div>

  <h3>Profiles</h3>
  <div class="block-template" draggable="true" data-type="github_user">GitHub User</div>
  <div class="block-template" draggable="true" data-type="github_repos">GitHub Repos</div>
  <div class="block-template" draggable="true" data-type="ip_info">IP Info</div>

  <h3>Roblox</h3>
  <div class="block-template" draggable="true" data-type="roblox_user">User by Name</div>
  <div class="block-template" draggable="true" data-type="roblox_user_by_id">User by ID</div>
  <div class="block-template" draggable="true" data-type="roblox_group">Group Info</div>
  <div class="block-template" draggable="true" data-type="roblox_user_groups">User's Groups</div>
  <div class="block-template" draggable="true" data-type="roblox_social">Social Counts</div>
  <div class="block-template" draggable="true" data-type="roblox_game">Game by Place ID</div>

  <h3>Entertainment</h3>
  <div class="block-template" draggable="true" data-type="recipes">Recipes (TheMealDB)</div>
  <div class="block-template" draggable="true" data-type="cocktails">Cocktails (TheCocktailDB)</div>
  <div class="block-template" draggable="true" data-type="anime">Anime (Jikan)</div>
  <div class="block-template" draggable="true" data-type="star_wars">Star Wars (SWAPI)</div>
  <div class="block-template" draggable="true" data-type="dnd_spell">DnD Spell</div>

  <h3>Live Data</h3>
  <div class="block-template" draggable="true" data-type="weather">Weather</div>
  <div class="block-template" draggable="true" data-type="geocode">Geocode</div>
  <div class="block-template" draggable="true" data-type="crypto">Crypto Prices</div>
  <div class="block-template" draggable="true" data-type="exchange">Currency Exchange</div>
  <div class="block-template" draggable="true" data-type="nasa_apod">NASA Picture of Day</div>
  <div class="block-template" draggable="true" data-type="sun_times">Sunrise / Sunset</div>
  <div class="block-template" draggable="true" data-type="world_time">World Time</div>

  <h3>News & Social</h3>
  <div class="block-template" draggable="true" data-type="reddit_top">Reddit Top Posts</div>
  <div class="block-template" draggable="true" data-type="hacker_news">Hacker News Top</div>

  <h3>Random / Fun</h3>
  <div class="block-template" draggable="true" data-type="joke">Dad Joke</div>
  <div class="block-template" draggable="true" data-type="joke_api">JokeAPI</div>
  <div class="block-template" draggable="true" data-type="cat_fact">Cat Fact</div>
  <div class="block-template" draggable="true" data-type="random_fact">Random Fact</div>
  <div class="block-template" draggable="true" data-type="advice">Advice</div>
  <div class="block-template" draggable="true" data-type="trivia">Trivia</div>
  <div class="block-template" draggable="true" data-type="random_user">Random User</div>
  <div class="block-template" draggable="true" data-type="quote">Quote</div>
  <div class="block-template" draggable="true" data-type="agify">Predict Age (Agify)</div>
  <div class="block-template" draggable="true" data-type="genderize">Predict Gender (Genderize)</div>

  <p class="small">Spotify and YouTube need API keys (already in .env).</p>
</div>

<div id="canvas">
  <h2>Workspace</h2>
  <p class="small"><button onclick="clearAll()">Clear all</button></p>
  <div id="drop" class="dropzone"></div>
</div>

</div>

<script src="/static/script.js"></script>

</body>
</html>
'''

FILES["static/script.js"] = r'''const BLOCKS = {
  // Search
  spotify_search: { title: "Spotify Search", fields: [
    {name: "query", label: "Query", type: "text"},
    {name: "type",  label: "Type",  type: "select", options: ["track","album","artist","playlist"]}
  ]},
  youtube_search: { title: "YouTube Search", fields: [{name: "query", label: "Query", type: "text"}]},

  // Lookups
  wikipedia:    { title: "Wikipedia",       fields: [{name: "title", label: "Title", type: "text"}]},
  dictionary:   { title: "Dictionary",      fields: [{name: "word", label: "Word", type: "text"}]},
  tv_shows:     { title: "TV Shows",        fields: [{name: "query", label: "Show name", type: "text"}]},
  books:        { title: "Books",           fields: [{name: "query", label: "Title / author", type: "text"}]},
  country_name: { title: "Country by Name", fields: [{name: "name", label: "Country", type: "text"}]},
  country_code: { title: "Country by Code", fields: [{name: "code", label: "ISO code (e.g. US, JP)", type: "text"}]},
  holidays:     { title: "Public Holidays", fields: [
    {name: "year",    label: "Year", type: "text"},
    {name: "country", label: "Country (e.g. US)", type: "text"}
  ]},
  pokemon:      { title: "Pokemon",         fields: [{name: "name", label: "Name", type: "text"}]},

  // Profiles
  github_user:  { title: "GitHub User",     fields: [{name: "username", label: "Username", type: "text"}]},
  github_repos: { title: "GitHub Repos",    fields: [{name: "username", label: "Username", type: "text"}]},
  ip_info:      { title: "IP Info",         fields: [{name: "ip", label: "IP (blank = yours)", type: "text"}]},

  // Roblox
  roblox_user:        { title: "Roblox User by Name", fields: [{name: "username", label: "Username", type: "text"}]},
  roblox_user_by_id:  { title: "Roblox User by ID",   fields: [{name: "user_id", label: "User ID", type: "text"}]},
  roblox_group:       { title: "Roblox Group",        fields: [{name: "group_id", label: "Group ID", type: "text"}]},
  roblox_user_groups: { title: "Roblox User's Groups",fields: [{name: "user_id", label: "User ID", type: "text"}]},
  roblox_social:      { title: "Roblox Social Counts",fields: [{name: "user_id", label: "User ID", type: "text"}]},
  roblox_game:        { title: "Roblox Game",         fields: [{name: "place_id", label: "Place ID", type: "text"}]},

  // Entertainment
  recipes:   { title: "Recipes",   fields: [{name: "query", label: "Recipe name", type: "text"}]},
  cocktails: { title: "Cocktails", fields: [{name: "query", label: "Cocktail name", type: "text"}]},
  anime:     { title: "Anime",     fields: [{name: "query", label: "Anime name", type: "text"}]},
  star_wars: { title: "Star Wars", fields: [{name: "query", label: "Character name (blank = first 10)", type: "text"}]},
  dnd_spell: { title: "DnD Spell", fields: [{name: "name", label: "Spell name (e.g. fireball)", type: "text"}]},

  // Live data
  weather:    { title: "Weather",     fields: [
    {name: "lat", label: "Latitude", type: "text"},
    {name: "lon", label: "Longitude", type: "text"}
  ]},
  geocode:    { title: "Geocode",     fields: [{name: "name", label: "Place", type: "text"}]},
  crypto:     { title: "Crypto",      fields: [{name: "ids", label: "IDs (e.g. bitcoin,ethereum)", type: "text"}]},
  exchange:   { title: "Currency",    fields: [
    {name: "base", label: "From (e.g. USD)", type: "text"},
    {name: "to",   label: "To (e.g. EUR,GBP)", type: "text"}
  ]},
  nasa_apod:  { title: "NASA APOD",   fields: [{name: "api_key", label: "API key (blank = DEMO_KEY)", type: "text"}]},
  sun_times:  { title: "Sun Times",   fields: [
    {name: "lat", label: "Latitude", type: "text"},
    {name: "lon", label: "Longitude", type: "text"}
  ]},
  world_time: { title: "World Time",  fields: [{name: "timezone", label: "TZ (e.g. Asia/Singapore)", type: "text"}]},

  // News & social
  reddit_top:  { title: "Reddit Top",  fields: [{name: "subreddit", label: "Subreddit", type: "text"}]},
  hacker_news: { title: "Hacker News", fields: [{name: "count", label: "How many (max 30)", type: "text"}]},

  // Random / fun
  joke:        { title: "Dad Joke",       fields: []},
  joke_api:    { title: "JokeAPI",        fields: [
    {name: "category", label: "Category", type: "select", options: ["Any","Programming","Misc","Pun","Spooky","Christmas"]},
    {name: "type",     label: "Type",     type: "select", options: ["any","single","twopart"]}
  ]},
  cat_fact:    { title: "Cat Fact",       fields: []},
  random_fact: { title: "Random Fact",    fields: []},
  advice:      { title: "Advice",         fields: []},
  trivia:      { title: "Trivia",         fields: [{name: "amount", label: "Count (default 5)", type: "text"}]},
  random_user: { title: "Random User",    fields: []},
  quote:       { title: "Quote",          fields: []},
  agify:       { title: "Predict Age",    fields: [{name: "name", label: "First name", type: "text"}]},
  genderize:   { title: "Predict Gender", fields: [{name: "name", label: "First name", type: "text"}]}
};

let blockCount = 0;
const RESPONSES = {};

document.querySelectorAll(".block-template").forEach(el => {
  el.addEventListener("dragstart", e => {
    e.dataTransfer.setData("type", el.dataset.type);
  });
});

const drop = document.getElementById("drop");
drop.addEventListener("dragover", e => { e.preventDefault(); drop.classList.add("over"); });
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", e => {
  e.preventDefault();
  drop.classList.remove("over");
  const type = e.dataTransfer.getData("type");
  if (type) addBlock(type);
});

function addBlock(type) {
  const def = BLOCKS[type];
  if (!def) return;
  blockCount++;
  const id = "blk" + blockCount;
  const div = document.createElement("div");
  div.className = "block";
  div.id = id;

  let html = `<h3>${def.title}</h3>`;
  for (const f of def.fields) {
    if (f.type === "select") {
      const opts = f.options.map(o => `<option value="${o}">${o}</option>`).join("");
      html += `<div><label>${f.label}:</label><select data-name="${f.name}">${opts}</select></div>`;
    } else {
      html += `<div><label>${f.label}:</label><input type="text" data-name="${f.name}"></div>`;
    }
  }
  html += `<div class="controls">
    <button class="run" onclick="runBlock('${id}', '${type}')">Run</button>
    <label style="margin-left:6px;">Display:
      <select onchange="render('${id}')" data-format>
        <option value="readable">Readable</option>
        <option value="raw">Raw JSON</option>
      </select>
    </label>
    <button onclick="removeBlock('${id}')" style="float:right;">Remove</button>
  </div>`;
  html += `<div class="output" style="display:none;"></div>`;

  div.innerHTML = html;
  drop.appendChild(div);
}

function removeBlock(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
  delete RESPONSES[id];
}

function clearAll() {
  drop.innerHTML = "";
  for (const k in RESPONSES) delete RESPONSES[k];
}

async function runBlock(id, type) {
  const el = document.getElementById(id);
  const out = el.querySelector(".output");
  out.style.display = "block";
  out.className = "output";
  out.textContent = "Running...";

  const body = {};
  el.querySelectorAll("[data-name]").forEach(inp => { body[inp.dataset.name] = inp.value; });

  try {
    const res = await fetch("/api/" + type, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    RESPONSES[id] = await res.json();
    render(id);
  } catch (err) {
    out.textContent = "Error: " + err.message;
  }
}

function render(id) {
  const el = document.getElementById(id);
  if (!el) return;
  const out = el.querySelector(".output");
  const fmt = el.querySelector("[data-format]").value;
  const resp = RESPONSES[id];
  if (!resp) return;

  if (fmt === "raw") {
    out.className = "output raw";
    out.textContent = "HTTP " + resp.status + "\n\n" + JSON.stringify(resp.data, null, 2);
  } else {
    out.className = "output";
    out.innerHTML = renderFormatted(resp.formatted);
  }
}

function renderFormatted(f) {
  if (!f) return "(no data)";
  if (f.type === "error")  return `<div class="err">${esc(f.message)}</div>`;
  if (f.type === "text")   return `<div>${esc(f.text).replace(/\n/g, "<br>")}</div>`;
  if (f.type === "fields") {
    let h = "<table>";
    for (const item of f.fields) {
      h += `<tr><th>${esc(item.label)}</th><td>${linkify(item.value)}</td></tr>`;
    }
    return h + "</table>";
  }
  if (f.type === "table") {
    let h = "<table><tr>";
    for (const head of f.headers) h += `<th>${esc(head)}</th>`;
    h += "</tr>";
    for (const row of f.rows) {
      h += "<tr>";
      for (const cell of row) h += `<td>${linkify(cell)}</td>`;
      h += "</tr>";
    }
    return h + "</table>";
  }
  return esc(JSON.stringify(f, null, 2));
}

function esc(s) {
  if (s == null) return "";
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function linkify(s) {
  const e = esc(s);
  if (typeof s === "string" && /^https?:\/\//.test(s)) {
    return `<a href="${e}" target="_blank">${e}</a>`;
  }
  return e;
}
'''

FILES["README.md"] = r'''# API Interactive

A drag-and-drop web app for calling public APIs live. Drag a block from the sidebar onto the canvas, fill in the inputs, hit Run. Each block has a Display toggle: **Readable** (default — table view) or **Raw JSON**.

## Setup

```
pip install -r requirements.txt
python run.py
```

## Modules

| File           | Purpose                                                              |
|----------------|----------------------------------------------------------------------|
| `http_util.py` | Loads `.env`, defines `safe_get` for plain GET requests              |
| `services.py`  | One function per API; returns `{status, data}`                       |
| `formatters.py`| One formatter per API; returns a structured display object         |
| `web.py`       | Flask app — single dispatcher route, looks up service+formatter     |
| `run.py`       | Entry point — imports `web.app` and starts the server                |

## Blocks (42 total, 8 categories)

### Search (2)
Spotify Search, YouTube Search

### Lookups (8)
Wikipedia, Dictionary, TV Shows (TVMaze), Books (Open Library), Country by Name, Country by Code, Public Holidays, Pokemon

### Profiles (3)
GitHub User, GitHub Repos, IP Info

### Roblox (6)
User by Name, User by ID, Group Info, User's Groups, Social Counts, Game by Place ID

### Entertainment (5)
Recipes (TheMealDB), Cocktails (TheCocktailDB), Anime (Jikan / MyAnimeList), Star Wars (SWAPI), DnD Spell (D&D 5e API)

### Live Data (7)
Weather, Geocode, Crypto Prices, Currency Exchange, NASA APOD, Sunrise/Sunset, World Time

### News & Social (2)
Reddit Top Posts, Hacker News Top

### Random / Fun (10)
Dad Joke, JokeAPI, Cat Fact, Random Fact, Advice, Trivia, Random User, Quote, Predict Age, Predict Gender

## Display formats

The Readable view picks the best layout per response shape:
- **text** — single string (jokes, facts, quotes, advice)
- **fields** — key/value pairs (weather, GitHub user, country detail, DnD spell)
- **table** — multiple rows (search results, top posts, holidays, recipes)

Switch to **Raw JSON** at any time. Switching is local and does not re-call.

## Notes on specific APIs

- **Spotify Search** — Spotify trimmed many fields from `/v1/search` in late 2024. Track results no longer carry `popularity`, and artist results no longer carry `followers` or `genres`. The formatter only displays what's still returned.
- **JokeAPI** filters out nsfw/religious/political/racist/sexist/explicit jokes by default.
- **DnD Spell** uses spell slug — for "Magic Missile" pass `magic-missile`. The block lowercases and replaces spaces automatically.
- **Star Wars (SWAPI)** uses swapi.info, which returns the entire People collection. Filtering happens server-side in `services.py`.
- **Roblox Game** chains: place ID → universe ID → game info.
- **Roblox Social Counts** chains 3 requests (friends + followers + following).
- **Hacker News Top** chains 1 + N requests (top story IDs, then each story).

## Adding a new block

1. Add a function to `services.py` returning `{status, data}`.
2. Add a formatter to `formatters.py` returning a `_text`, `_fields`, or `_table` structure.
3. Register the block in the `HANDLERS` map in `web.py`.
4. Add a draggable element in `templates/index.html` under the right category.
5. Add an entry in the `BLOCKS` object in `static/script.js`.
'''

FILES["requirements.txt"] = "flask\nrequests\npython-dotenv\n"

FILES[".env"] = (
    f"SPOTIFY_CLIENT_ID={SPOTIFY_CLIENT_ID}\n"
    f"SPOTIFY_CLIENT_SECRET={SPOTIFY_CLIENT_SECRET}\n"
    f"YOUTUBE_API_KEY={YOUTUBE_API_KEY}\n"
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
