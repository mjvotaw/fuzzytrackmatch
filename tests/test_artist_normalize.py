from fuzzytrackmatch.song_normalize import normalize_title_and_artists



def test_multiple_artists_in_artist():

  title = "Some Song"
  artist = "Artist1 & Artist2"

  result = normalize_title_and_artists(artist, title)
  assert len(result.artists) == 2
  assert result.artists[0] == "Artist1"
  assert result.artists[1] == "Artist2"


def test_multiple_artists_in_title():

  title = "Some Song (ft. Artist2 & Artist3)"
  artist = "Artist1"

  result = normalize_title_and_artists(artist, title)

  assert result.title == "Some Song"
  assert len(result.artists) == 3
  assert result.artists[0] == "Artist1"
  assert result.artists[1] == "Artist2"
  assert result.artists[2] == "Artist3"

def test_multiple_artists_in_subtitle():
  title = "Some Song"
  subtitle = "(ft. Artist2 & Artist3)"
  artist = "Artist1"

  result = normalize_title_and_artists(artist, title, subtitle)

  assert result.title == title
  assert len(result.artists) == 3
  assert result.artists[0] == "Artist1"
  assert result.artists[1] == "Artist2"
  assert result.artists[2] == "Artist3"

def test_duplicate_artist_names():
  """What if they've somehow managed to define the additional artists in multiple places"""
  title = "Some Song"
  subtitle = "(ft. Artist2 & Artist3)"
  artist = "Artist1, Artist2 & Artist3"

  result = normalize_title_and_artists(artist, title, subtitle)

  assert result.title == title
  assert len(result.artists) == 3
  assert result.artists[0] == "Artist1"
  assert result.artists[1] == "Artist2"
  assert result.artists[2] == "Artist3"

def test_just_one_artist():
  """Sanity check that track titles don't get split up unexpectedly"""
  title = "Some Song (with stuff in parentheses, & characters that might trigger artist splitting)"
  artist = "Artist1"

  result = normalize_title_and_artists(artist, title)

  assert result.title == title


def test_artist_vs_artist():
  title = "Some Song"
  artist = "Artist1 vs Artist2"
  result = normalize_title_and_artists(artist, title)

  assert len(result.artists) == 2
  assert result.artists[0] == "Artist1"
  assert result.artists[1] == "Artist2"

  artist = "Artist1 vs. Artist2"
  result = normalize_title_and_artists(artist, title)

  assert len(result.artists) == 2
  assert result.artists[0] == "Artist1"
  assert result.artists[1] == "Artist2"
