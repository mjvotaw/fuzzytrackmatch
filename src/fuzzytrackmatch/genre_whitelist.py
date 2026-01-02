# The contents of this file are primarily based on the 'lastgenre' plugin from the music library manager Beets ( https://beets.io/ )
# Original file can be found at https://github.com/beetbox/beets/blob/master/beetsplug/lastgenre/__init__.py
#
# Copyright 2016, Adrian Sampson.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

import os
import yaml
from dataclasses import dataclass

@dataclass
class GenreTag:
  name: str
  score: float

  @classmethod
  def from_dict(cls, data):
    return cls(
      name=data.get('name'),
      score=data.get('score')
    )


C14N_TREE_FILEPATH = os.path.join(os.path.dirname(__file__), "genres-tree.yaml")
GENRE_ALIASES_FILEPATH = os.path.join(os.path.dirname(__file__), "genre-aliases.yaml")

def deduplicate(seq):
  """Remove duplicates from sequence while preserving order."""
  seen = set()
  return [x for x in seq if x not in seen and not seen.add(x)]

def remove_subsets(list_of_lists: list[list[str]]):
  """Remove lists from the sequence that are a subset of another list."""
  result = []

  for i, sublist1 in enumerate(list_of_lists):
    is_subset = False

    for j, sublist2 in enumerate(list_of_lists):
      if i != j and set(sublist1).issubset(set(sublist2)):
        is_subset = True
        break

    if not is_subset:
      result.append(sublist1)

  return result


def flatten_tree(data):
  result = []
  
  def flatten(item):
    if isinstance(item, dict):
      for key, value in item.items():
        result.append(key)
        flatten(value)
    elif isinstance(item, list):
      for element in item:
        flatten(element)
    elif isinstance(item, str):  # Only strings
      result.append(item)
  
  flatten(data)
  return result

def get_tree_paths(elem):
  """Extract all root-to-leaf paths from nested lists/dictionaries.
  """
  def tree_paths(elem, path, branches):
    if not path:
      path = []

    if isinstance(elem, dict):
      for k, v in elem.items():
        tree_paths(v, path + [k], branches)
    elif isinstance(elem, list):
      for sub in elem:
        tree_paths(sub, path, branches)
    else:
      branches.append(path + [str(elem)])
  branches = []

  tree_paths(elem, [], branches)
  return branches


def find_parents(candidate, branches):
  """Find parents genre of a given genre, ordered from the closest to
  the further parent. Returns a list of genres, including the given
  `candidate` genre, and parent genres
  """
  for branch in branches:
    try:
      idx = branch.index(candidate.lower())
      return list(reversed(branch[: idx + 1]))
    except ValueError:
      continue
  return [candidate]


def normpath(path):
  """Provide the canonical form of the path suitable for storing in
  the database.
  """
  path = os.path.normpath(os.path.abspath(os.path.expanduser(path)))
  return path

def load_whitelist(wl_filename):
  """Load a genre whitelist from the given wl_filename. 
  """
  whitelist = set()
  c14n_filename = normpath(wl_filename)
  with open(c14n_filename, "r", encoding="utf-8") as f:
    genres_tree = yaml.safe_load(f)
    flattened_list = flatten_tree(genres_tree)
    whitelist.update(flattened_list)
  return whitelist

def load_c14n_tree(c14n_filename):
  c14n_filename = normpath(c14n_filename)
  with open(c14n_filename, "r", encoding="utf-8") as f:
    genres_tree = yaml.safe_load(f)
    c14n_branches = get_tree_paths(genres_tree)
    return c14n_branches

def load_aliases(aliases_filename):
  aliases_filename = normpath(aliases_filename)
  with open(aliases_filename, "r", encoding="utf-8") as f:
    genre_aliases = yaml.safe_load(f)
    return genre_aliases

class GenreWhitelist:

  def __init__(self):
    self.whitelist = load_whitelist(C14N_TREE_FILEPATH)
    self.c14n_branches = load_c14n_tree(C14N_TREE_FILEPATH)
    self.genre_aliases = load_aliases(GENRE_ALIASES_FILEPATH)

  def resolve_genre(self, tag: str, count:int=10):
    genre_tag = GenreTag(name=tag, score=1)
    return self.resolve_genres([genre_tag], count)
  
  def resolve_genres(self, tags:list[GenreTag], count:int=10) -> list[list[GenreTag]]:
    """
    Resolves the given tags to so-called 'canonical' names.
    The 'canonical' name is a list of genres and parent genres.
    This data is based on 

    Returns a list of list of genre names

    Example:
    if `tags` = ["psytrance"], this will return 
    ```
    [
      [ 'Psytrance', 'Goa Trance', 'Trance']
    ]
    ```  
     """
    if not tags:
      return []

    tag_names = [self.normalize_tag(tag.name) for tag in tags]
    tag_names = deduplicate([t for t in tag_names if t is not None])

    tags_all: list[list[str]] = []
    for tag in tag_names:
      parents = find_parents(tag, self.c14n_branches)
      if len(parents) > 0:
        tags_all.append(parents)
    
    canonized_tag_names = remove_subsets(tags_all)
    tag_scores = self._sum_tag_scores(tags)
    canonized_genre_tags = [[GenreTag(name=tag.title(), score=tag_scores[tag] if tag in tag_scores else 1) for tag in group] for group in canonized_tag_names]
    return canonized_genre_tags
    
  def _sum_tag_scores(self, tags: list[GenreTag]):
    tag_scores: dict[str, float] = {}
    for tag in tags:
      tag_name = self.normalize_tag(tag.name)
      if tag_name is None:
        continue
      if tag_name not in tag_scores:
        tag_scores[tag_name] = 0
      tag_scores[tag_name] += tag.score
    return tag_scores
  
  def _get_depth(self, tag):
    """Find the depth of a tag in the genres tree."""
    depth = None
    for key, value in enumerate(self.c14n_branches):
      if tag in value:
        depth = value.index(tag)
        break
    return depth

  def _sort_by_depth(self, tags):
    """Given a list of tags, sort the tags by their depths in the
    genre tree.
    """
    depth_tag_pairs = [(self._get_depth(t), t) for t in tags]
    depth_tag_pairs = [e for e in depth_tag_pairs if e[0] is not None]
    depth_tag_pairs.sort(reverse=True)
    return [p[1] for p in depth_tag_pairs]
  
  def _format_tag(self, tag):
    return tag.title()
  
  def is_allowed(self, genre):
    """Determine whether the genre is present in the whitelist,
    returning a boolean.
    """
    if genre is None:
      return False
    if genre in self.whitelist:
      return True
    return False
  
  def find_alias(self, tag:str):
    """Find the canonical name for the given tag, if the tag is
    a known alias of a genre."""
    for genre, aliases in self.genre_aliases.items():
      if tag in aliases:
        return genre
    
    return None

  def normalize_tag(self, tag:str):
    """Tries to figure out if some variation of the given tag exists in our whitelist.
    If so, returns that variant, otherwise returns None
    """

    tag = tag.lower()

    if tag in self.whitelist:
      return tag
    
    # is the tag a common alias of a known genre?
    alias = self.find_alias(tag)
    if alias is not None:
      return alias
    
    # the tag might have hyphens when our whitelist doesn't expect
    if "-" in tag:
      tag = tag.replace("-", " ")
      if tag in self.whitelist:
        return tag
    
    # the tag might have a variation on "and" that isn't expected
    and_replacements = ["'n'", " n ", " & "]
    for and_replacement in and_replacements:
      if and_replacement in tag:
        tag = tag.replace(and_replacement, " and ")
        tag = tag.replace("  ", " ")
    
    if tag in self.whitelist:
      return tag
  
    return None
