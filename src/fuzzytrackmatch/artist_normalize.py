from dataclasses import dataclass
import re

anyFeat = re.compile(r"( |\()feat[. ]", re.IGNORECASE);    # does the string contain "feat." or "feat "?
featWithParen = re.compile(r"\(feat[\.| ].*?\)", re.IGNORECASE) # does the string contain "(feat.<something>)" or "(feat <something>)"?
featWithSpace = re.compile(r" feat[. ].*?$", re.IGNORECASE)    # does the string contain " feat.<something>" or " feat <something>"?

@dataclass
class NormalizedSongInfo:
    title: str
    subtitle: str
    artists: list[str]  

def normalize_title_and_artists(title:str, subtitle:str, artist:str):
    '''
Attempts to normalize the given title, subtitle, and artist by 
splitting the `artist` string into multiple artist names, and
checking `title` and `subtitle` to see if they also  contain
any secondary artist names.'''
    artists = split_artists(artist)

    if anyFeat.search(title) != None:
        split = separate_title_and_artist(title)
        title = split[0]
        artists = artists + split[1]

    if anyFeat.search(subtitle) != None:
        split = separate_title_and_artist(subtitle)
        subtitle = split[0]
        artists = artists + split[1]
    
    return NormalizedSongInfo(title=title, subtitle=subtitle, artists=artist)


def separate_title_and_artist(title:str):
    '''
Sometimes song titles or subtitles will include things like "Feat. so 'n so",
instead of it being in the artist string. So we need to split the 
artist/artists from the rest of the title.
'''
    match = featWithParen.search(title)
    if match is None:
        match = featWithSpace.search(title)
    
    if match != None:
        artists = split_artists(match[0])
        title = title.replace(match[0], "")
        return (title.strip(), artists)
    
    return (title, [])
    

def split_artists(artist: str):
    '''
An "artist" tag might actually be several artists ("Srezcat [feat. blaxervant & Shinonome I/F]")
We need to split this up into multiple artist names so that we can provide a better search query
and to provide more accurate scoring.
We don't sort this list here, because we want to preserve the order of the artists,
the assumption being that the first artist is the main artist of the song.
    '''
    original_artist = artist

    separators = [" & ", " + ", " feat. ", " feat ", " ft. ", "vs. ", " vs ", ", ", " + ", " x "]
    replacement_separator = "----sep----"

    chars_to_strip = ["(", ")", "[", "]"]

    # Replace characters we don't want with spaces, which will get trimmed out in the end
    for c in chars_to_strip:
        artist = artist.replace(c, " ")
    
    # Replace any separators with a common string that (hopefully) won't otherwise be present,
    # so we can then split artist into multiple artists
    for s in separators:
        pat = re.compile(s, re.IGNORECASE)
        artist = pat.sub(replacement_separator, artist)

    split_artists = artist.split(replacement_separator)
    split_artists = [a.strip() for a in split_artists if a.strip()!= '']

    # If for some reason we end up with an empty array, just return the original artist value
    if len(split_artists) == 0:
        split_artists = [original_artist]
    
    return split_artists