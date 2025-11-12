from fuzzytrackmatch import DiscogsSearch

discogs = DiscogsSearch(api_key="YOUR_USER_KEY_HERE")

results = discogs.fetch_track_genres("Nirvana", "Smells like Teen Spirit", None)
if results:
  print(results.track.title)
  print(results.genres)
  print(results.canonicalized_genres)
