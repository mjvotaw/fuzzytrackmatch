# The contents of this file are primarily from the 'lastgenre' plugin from the music library manager Beets ( https://beets.io/ )
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

import codecs
import os
import yaml
from .base_genre_search import GenreTag


# default genre whitelist data was scraped from Wikipedia.
# The scraper script is available at: https://gist.github.com/1241307

WHITELIST = os.path.join(os.path.dirname(__file__), "genres.txt")
C14N_TREE = os.path.join(os.path.dirname(__file__), "genres-tree.yaml")

def deduplicate(seq):
    """Remove duplicates from sequence while preserving order."""
    seen = set()
    return [x for x in seq if x not in seen and not seen.add(x)]

def remove_subsets(list_of_lists):
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


def flatten_tree(elem, path, branches):
    """Flatten nested lists/dictionaries into lists of strings
    (branches).
    """
    if not path:
        path = []

    if isinstance(elem, dict):
        for k, v in elem.items():
            flatten_tree(v, path + [k], branches)
    elif isinstance(elem, list):
        for sub in elem:
            flatten_tree(sub, path, branches)
    else:
        branches.append(path + [str(elem)])


def find_parents(candidate, branches):
    """Find parents genre of a given genre, ordered from the closest to
    the further parent.
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
    wl_filename = normpath(wl_filename)
    with open(wl_filename, "rb") as f:
        for line in f:
            line = line.decode("utf-8").strip().lower()
            if line and not line.startswith("#"):
                whitelist.add(line)
    return whitelist

def load_c14n_tree(c14n_filename):
    c14n_branches = []
    # Read the tree
    c14n_filename = normpath(c14n_filename)
    with codecs.open(c14n_filename, "r", encoding="utf-8") as f:
        genres_tree = yaml.safe_load(f)
    flatten_tree(genres_tree, [], c14n_branches)
    
    return c14n_branches

class GenreWhitelist:

    def __init__(self):
        self.whitelist = load_whitelist(WHITELIST)
        self.c14n_branches = load_c14n_tree(C14N_TREE)
    
    def resolve_genres(self, tags:list[str], count) -> list[list[str]]:
        """
        Resolves the given tags to so-called 'canonical' names.
        The 'canonical' name is a list of genres and parent genres.
        This data is based on 

        Returns a list of list of genre names

        Example:
        if `tags` = ["dubstep"], this will return 
        ```
        [
            [ 'Dubstep', 'Uk Garage', 'Dance']
        ]
        ```  
         """
        if not tags:
            return []

        tag_names = [tag.lower() for tag in tags]
        tag_names = [self.normalize_tag(tag) for tag in tag_names]
        tag_names = deduplicate([t for t in tag_names if t is not None])
        
        # Extend the list to consider tags parents in the c14n tree
        tags_all = []
        for tag in tag_names:
            # Add parents that are in the whitelist, or add the oldest
            # ancestor if no whitelist
            parents = [
                x
                for x in find_parents(tag, self.c14n_branches)
                if self.is_allowed(x)
            ]

            if len(parents) > 0:
                tags_all.append(parents)
    
            # Stop if we have enough tags already, unless we need to find
            # the most specific tag (instead of the most popular).
            if len(tags_all) >= count:
                break
        
        tag_names = remove_subsets(tags_all)
        tag_names = [[self._format_tag(x) for x in group if self.is_allowed(x)] for group in tag_names]

        return tag_names[: count]

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

        if "-" in genre:
            genre = genre.replace("-", " ")
            if genre in self.whitelist:
                return True
        return False
    
    def normalize_tag(self, tag:str):
        """Tries to figure out if some variation of the given tag exists in our whitelist.
        If so, returns that variant, otherwise returns None
        """
        if tag in self.whitelist:
            return tag
        
        if "-" in tag:
            tag = tag.replace("-", " ")
            if tag in self.whitelist:
                return tag
    
        return None
