# fuzzytrackmatch

> **NOTE:** this is very much a work in progress.

## what is it

This is a small library for searching sources of music data (eg [last.fm](https://www.last.fm), [discogs](https://www.discogs.com/)) for tracks based on not-quite-correct titles and artist names. It also tries to normalize returned genre information based on user-contributed tags.

A basic example:

```python
from fuzzytrackmatch import LastFMSearch

l = LastFMSearch(api_key="YOUR_API_KEY_HERE")

result = l.fetch_track_genres("Usher", "Yeah!", "(feat. Lil Jon & Ludacris)")

if results:
  print(results.track.title)
  print(result.track.artists)
  print(result.track.source_url)
  print(results.genres)
  print(results.canonicalized_genres)
```

## ok cool but why

I needed a tool to help me retrieve some song info, particularly genres, for a large set of user-provided track titles and artists. Turns out, people have different ideas on how to include things like additional artists or subtitles.

## Normalizing Artist Names

Take, for instance, the song "Yeah!" by Usher, featuring Lil Jon and Ludacris. Some people might write the "artist" field as "Usher feat. Lil Jon & Ludacris", which is a problem, because lots of music platforms attribute songs to one and only one artist. Some people and platforms include it as part of the title, like "Yeah! (feat. Lil Jon, Ludacris)". Some people might include it as part of the "subtitle" field, which apparently isn't a thing on a lot of music platforms.

So this library does some work to clean up the user input and split additional artists into an array of artist names before searching the music platform. It then uses [SequenceMatcher](https://docs.python.org/3/library/difflib.html) to do some basic sanity checking of the return results to find the best matching track.

## Canonicalized Genres

Genre information is derived from user-submitted data (eg 'tags' in last.fm). This makes use of an algorithm that's largely based on work from the [lastgenre plugin](https://github.com/beetbox/beets/blob/master/beetsplug/lastgenre/__init__.py)
 from the [beets media library manager](https://beets.io/). It filters and normalizes data based on a genre whitelist that is made primarily of data scraped from Wikipedia. At some point, I modified the whitelist to group dance music genres under an umbrella "dance" genre, to better suit my personal needs.

 Given a list of possible genre tags, each tag is checked against a whitelist of "known" genres, if it's found, then a "canonicalized genre" is found for it, which is just list that contains that genre and it's parent genres.

 So for instance, if given the genre "happy hardcore", the `GenreWhitelist.resolve_genre` method would return `[["Happy Hardcore", "Hardcore", "Dance"]]`.


## known problems

Currently, last.fm's api doesn't consistently return `tags` information for all tracks.

## Todos:
- add option to cache network data
- 