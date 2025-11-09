from fuzzytrackmatch.lastfm_search import LastFMSearch

l = LastFMSearch(api_key="YOUR_API_KEY_HERE")

result = l.fetch_artist_genres("Pegboard Nerds feat. Elizaveta")

print(result)
