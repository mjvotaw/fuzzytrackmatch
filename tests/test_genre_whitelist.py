from fuzzytrackmatch.genre_whitelist import GenreWhitelist
wh = GenreWhitelist()

# basic sanity tests for changes made to genres-tree.yaml

def test_find_dubstep():
  genres = wh.resolve_genre('dubstep')
  assert len(genres) == 1
  assert genres[0][0].name == "Dubstep"

def test_find_cpop():
  genres = wh.resolve_genre("c-pop")
  assert genres[0][0].name == "C-Pop"


# tests for not-quite-matching genre names
def test_find_drum_n_bass():
  genres = wh.resolve_genre("drum 'n' bass")
  assert len(genres) == 1
  assert genres[0][0].name == "Drum And Bass"