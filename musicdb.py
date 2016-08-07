import json
import os
import eyed3
from tinytag import TinyTag
from shutil import copy2
from urllib.parse import quote
from hashlib import sha1
"""
tag.album         # album as string
tag.albumartist   # album artist as string
tag.artist        # artist name as string
tag.audio_offset  # number of bytes before audio data begins
tag.bitrate       # bitrate in kBits/s
tag.disc          # disc number
tag.disc_total    # the total number of discs
tag.duration      # duration of the song in seconds
tag.filesize      # file size in bytes
tag.genre         # genre as string
tag.samplerate    # samples per second
tag.title         # title of the song
tag.track         # track number as string
tag.track_total   # total number of tracks as string
tag.year          # year or data as string

tag = TinyTag.get('/some/music.mp3', image=True)
tag.get_image()
"""

fields = ('album', 'albumartist', 'artist', 'title', 'genre', 'track', 'year', 'plays', 'img', 'bitrate', 'lyrics', 'duration', 'uid', 'size', 'sorted')
fields_mod = ('album', 'albumartist', 'artist', 'title', 'genre', 'track', 'year', 'plays', 'img', 'lyrics')

root_dir = '/media/eli/shorty/music/'
backup_dir = root_dir + 'cfg/backup/'
library_dir = root_dir + 'library/'
import_dir = root_dir + 'import/'
source_dir = '/home/eli/Dropbox/code/player/source/'
asset_dir = source_dir + 'assets'
index_tpl = source_dir + 'index.tpl'
db_file = source_dir + 'musicdb.json'




def buildDB(contents): #takes dictionary and dumps it
    print(contents)
    with open(db_file, 'w', encoding='utf-8') as outfile:
        json.dump(contents, outfile, sort_keys = True, indent = 4, ensure_ascii = False)

def addToLibrary(song, artist, title): #Renames file, copies, and returns new file name
    if artist[0].isalpha() == True:
        first_let = artist[0].lower()
    else:
        first_let = '0'
    artist_dir = library_dir + first_let + os.sep
    filename = artist + '_' + title
    fileext = os.path.splitext(song)[1]
    dup_count = 1
    while os.path.exists(artist_dir + filename + fileext) == True:
        filename = artist + '_' + title + '_' + str(dup_count)
        dup_count += 1
    copy2((root_dir + song), (artist_dir + filename + fileext))
    return (filename + fileext)

def getImports(): #returns list of only files in /music
    root_path = os.listdir(root_dir)
    root_list = []
    for i in root_path:
        #name = str(i)
        if os.path.isdir(root_dir + i):
            continue
        else:
            root_list.append(i)
    return root_list

def getTag(song_path): #returns all matching fields
    tag = TinyTag.get(song_path)
    tag_fields = tag.__dict__
    details = {}
    for item in tag_fields:
        if item in fields and tag_fields[item] != None:
            details[item] = tag_fields[item]
    details['duration'] = "{:.2f}".format(details.get('duration'))
    if details.get('bitrate') > 5000:
        details.pop('bitrate')
    return details

def openDB(): #returns contents of musicdb
    with open(db_file, 'r', encoding='utf-8') as db_json:
        db = json.load(db_json)
        db_json.close()
        return db

def updateTag(song_path, tag_dict):
    song_file = eyed3.load(song_path)
    song_file.initTag(version=(2, 3, 0))
    if tag_dict.get('title') and tag_dict.get('title') != None:
        song_file.tag.title = tag_dict.get('title')
    if tag_dict.get('albumartist') and tag_dict.get('albumartist') != None:
        song_file.tag.album_artist = tag_dict.get('albumartist')
    if tag_dict.get('artist') and tag_dict.get('artist') != None:
        song_file.tag.artist = tag_dict.get('artist')
    if tag_dict.get('album') and tag_dict.get('album') != None:
        song_file.tag.album = tag_dict.get('album')
    if tag_dict.get('genre') and tag_dict.get('genre') != None:
        song_file.tag.genre = tag_dict.get('genre')
    if tag_dict.get('track') and tag_dict.get('track') != None:
        song_file.tag._setTrackNum(int(tag_dict.get('track')))
    if tag_dict.get('year') and tag_dict.get('year') != None:
        song_file.tag._setReleaseDate(tag_dict.get('year'))
    if tag_dict.get('plays') and tag_dict.get('plays') != None:
        song_file.tag.playcount(int(tag_dict.get('plays')))
    song_file.tag.save(preserve_file_time=True)
    print('success')

def getArtistDir(artist):
    if artist[0].isalpha() == True:
        first_let = artist[0].lower()
    else:
        first_let = '0'
    artist_dir = first_let + os.sep
    return artist_dir

def emptyDB():
    organizer = dict(last_id = 0, ignore_dirs = ['cfg', 'library', 'import'], ids =  {})
    return organizer

def chunkReader(fobj, chunk_size=1024):
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk

organizer = openDB()

def checkForDups(file_hash):
    ids = openDB().get('ids')
    for item in ids:
        if ids[item]['uid'] == file_hash:
            print("DUP BITCH")
            return True
    return False

def addToDB(song, hash=sha1):
    print("adding")
    song_path = root_dir + song

    hash_obj = hash()
    for chunk in chunkReader(open(song_path, 'rb')):
        hash_obj.update(chunk)
    file_id = (hash_obj.digest(), os.path.getsize(song_path))
    file_hash = str(file_id[0])

    if checkForDups(file_hash):
        print('sorry')
    else:
        ids = organizer.get('ids')
        tags = getTag(song_path)
        last_id = organizer.get("last_id")
        print(last_id)
        new_id = last_id + 1
        while new_id in ids:
            new_id += 1
        ids[new_id] = tags.copy()
        id_entry = ids[new_id]

        id_entry['uid'] = file_hash
        id_entry['size'] = file_id[1]

        artist = tags.get('artist')
        title = tags.get('title')
        if artist != None and title != None:
            id_entry['file'] = addToLibrary(song, artist, title)
            id_entry['sorted'] = True
        else:
            id_entry['file'] = song
            id_entry['sorted'] = False
        organizer['last_id'] = new_id
        print(organizer.items())
        buildDB(organizer)
    return 'susss'


def getAllIDs():
    id_db = openDB()
    ids = id_db.get('ids')
    id_list = []
    for num in ids:
        id_list.append(num)
    return id_list

def getLibraryIDs():
    id_db = openDB()
    ids = id_db.get('ids')
    id_list = []
    for num in ids:
        if ids[num]['sorted'] == True:
            id_list.append(num)
    return id_list

def getByID(song_id):
    id_db = openDB()
    ids = id_db.get('ids')
    for num in ids:
        if num == str(song_id):
            return ids[num]
    return False
##NEED TO CHOWN ELI:ELI 755 ALL FILES IN MUSIC
