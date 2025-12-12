from fuzzytrackmatch.genre_whitelist import GenreWhitelist, flatten_tree

# Test to make sure that our whitelist doesn't contain duplicate entries
def test_genre_uniqueness():
  wl = GenreWhitelist()
  unique_whitelist = set(wl.whitelist)
  assert len(wl.whitelist) == len(unique_whitelist)

# Test to make sure that our list of aliases doesn't contain duplicate entries
def test_alias_uniqueness():
  wl = GenreWhitelist()
  aliases = flatten_tree(wl.genre_aliases)
  unique_aliases = set(aliases)
  assert len(aliases) == len(unique_aliases)

# Test to make sure that all of the canonical genre names in our list of aliases
# are actually in our whitelist
def test_alias_keys_in_whitelist():
  wl = GenreWhitelist()
  alias_keys = wl.genre_aliases.keys()

  whitelist = wl.whitelist
  for a in alias_keys:
    assert a in whitelist


# Test to make sure that the aliases in our list of genre aliases aren't
# part of our whitelist
def test_aliases_not_in_whitelist():
  wl = GenreWhitelist()
  
  for aliases in wl.genre_aliases.values():
    for a in aliases:
      assert a not in wl.whitelist