import json
import os
import taglib
import eyed3
import re
import unicodedata
import logging
import time
from shutil import copy2, rmtree
from urllib.parse import quote
from hashlib import sha1


fields = ('album', 'albumartist', 'artist', 'title', 'genre', 'track', 'year', 'plays', 'img', 'bitrate', 'lyrics', 'length', 'uid', 'size', 'sorted')
fields_mod = ('album', 'albumartist', 'artist', 'title', 'genre', 'track', 'year')
fields_lib = ('album', 'artist', 'title', 'track', 'year', 'bitrate', 'length', 'img', 'plays')
root_dir = '/media/eli/shorty/music/'
static_dir='static/'
cfg_dir = root_dir + 'cfg/'
extras_dir = cfg_dir + 'extras/'
dup_dir = extras_dir + 'duplicates/'
trash_dir = extras_dir + 'trashes/'
art_dir = extras_dir + 'albumart/'
backup_dir = '/media/eli/blocks/player/backup/'
library_dir = root_dir + 'library/'
import_dir = root_dir + 'import/'
source_dir = cfg_dir + 'source/'
asset_dir = extras_dir + 'assets/'
index_tpl = source_dir + 'index.tpl'
db_file = source_dir + 'musicdb.json'
db_lock = source_dir + "musicdb.lock"
db_empty = dict(last_id = 0, ids =  {}, artists = [], duplicates = {})
supported_imgs = ('.jpg', '.jpeg', '.png')
supported_audio = ('.mp3', '.ogg', '.opus', '.m4a', '.flac', '.wma', '.wav')
with open(source_dir + 'changelog.txt', 'r') as changelog:
    version_info = changelog.readline()


logger = logging.getLogger('musicdb')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(cfg_dir + "logs/" + '.'.join(map(str,time.localtime()[0:3]))+ "_debug.log")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
fh.setFormatter(formatter)
logger.addHandler(fh)


############-blatantly stolen functions-###############

def chunkReader(fobj, chunk_size=1024):
    """Generator that reads a file in chunks of bytes"""
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk

def newHash(file, hash=sha1):
    hash_obj = hash()
    for chunk in chunkReader(open(file, 'rb')):
        hash_obj.update(chunk)
    file_hash = hash_obj.digest()
    return str(file_hash)

def getValidFileName(string):
    '''
    strips leading and trailing spaces
    and anything that is not a unicode alphanumeric, dash, underscore, or dot, is removed.
    '''
    string = unicodedata.normalize('NFKD', str(string).strip()).encode('ascii', 'ignore')
    string = re.sub(r'[^\w\s-]', '', string.decode('ascii'))
    string = ' '.join(string.split())
    return string

#====================================================================================================================================================
#=======================================================================DATABASE=====================================================================
#====================================================================================================================================================

def isDBLocked():
    if os.path.exists(db_lock) == False:
        return False
    else:
        logger.info('ERROR: Attempted to access locked DB')
        return True

def lockDB():
    open(db_lock,'a').close()

def unlockDB():
    os.remove(db_lock)

def renewDB(): #returns contents of musicdb
    if not isDBLocked():
        lockDB()
        with open(db_file, 'r', encoding='utf-8') as db_json:
            db = json.load(db_json)
            db_json.close()
            unlockDB()
            db_organizer = db
            return db
    else:
        logger.info("ERROR: DB Locked")
        return False

db_organizer = renewDB()

def buildDB(database): #takes dictionary and dumps it
    if not isDBLocked():
        lockDB()
        with open(db_file, 'w', encoding='utf-8') as outfile:
            json.dump(database, outfile, sort_keys = True, indent = 4, ensure_ascii = False)
        unlockDB()
        return True
    else:
        return False

def buildEmptyDB():
    database = db_empty
    if not isDBLocked():
        lockDB()
        with open(db_file, 'w', encoding='utf-8') as outfile:
            json.dump(database, outfile, sort_keys = True, indent = 4, ensure_ascii = False)
        unlockDB()
        return True
    else:
        return False

def createDBEntry(file_path): # call after moving file
    ids = db_organizer.get('ids').keys()
    last_id = db_organizer.get("last_id")
    new_id = last_id + 1
    while new_id in ids:
        new_id += 1
    tags = getFileTag(file_path)
    tag_dict = tags.copy()
    #id_entry = ids[new_id]
    tag_dict['uid'] = {}
    uids = tag_dict['uid']
    uids[(newHash(file_path))] = ""
    artist = tag_dict.get('artist')
    title = tag_dict.get('title')
    if artist and title:
        tag_dict['sorted'] = True
    else:
        tag_dict['sorted'] = False
    tag_dict['file'] = str(os.path.split(file_path)[1])
    tag_dict['plays'] = 0
    tag_dict['lyrics'] = False
    for k in tag_dict.keys():
        if (type(tag_dict[k]) == type("")):
            tag_dict[k] = tag_dict[k].replace("\"", "'")
            tag_dict[k] = tag_dict[k].replace("\\", "")
            tag_dict[k] = remove_non_ascii(tag_dict[k])
    logger.info("Creating id dict for " + str(new_id) + str(file_path))
    return (new_id, tag_dict)

def addToDuplicateList(file_path, orig_file):
    file_name = os.path.split(file_path)[1]
    logger.info("[Duplicate] added: " + str(file_path) + ". Original: " + str(orig_file))
    db_organizer['duplicates'][file_name] = orig_file

def addArtistToSet(artist):
    artists = db_organizer.get('artists')
    if artist not in artists:
        artists.append(artist)

def removeArtistFromSet(artist):
    artist_dir = getArtistDir(artist)
    for song in os.listdir(library_dir + artist_dir):
        if song.startswith(artist) == True:
            return False # return false if artist found
    artists = db_organizer.get('artists')
    artists.remove(artist)
    return True

def addID(song_id, db_tag):
    ids = db_organizer.get('ids')
    ids[str(song_id)] = db_tag.copy()
    db_organizer["last_id"] = song_id
    logger.info("[Added] id " + str(song_id))

def updateID(song_id, tag_dict):
    ids = db_organizer.get('ids')
    id_entries = ids[str(song_id)]
    if tag_dict.get('uid'):
        id_entries['uid'][tag_dict.get('uid')] = ""
        del tag_dict['uid']
    for k, v in tag_dict.items():
        if v == "" and id_entries.get(k):
            del id_entries[k]
        else:
            id_entries[k] = v
    logger.info("[Updated] id " + str(song_id))
    buildDB(db_organizer)

#====================================================================================================================================================
#=======================================================================FILE MANAGEMENT==============================================================
#====================================================================================================================================================

def checkImports():
    '''
    searches imports for files
    pulls out supported audio files
    -ignores if still being copied/modified
    picks a supported image in each folder
    returns [('path', [songs], 'img'), ...]
    returns False if no songs found
    '''
    song_list = [] # all songs
    for (path, dirs, files) in os.walk(import_dir):
        songs = [] #songs per dir
        img = '' # img per dir
        if path[-1:] != "/":
            path += "/"
        if len(files) > 0:
            for item in files:
                if os.path.splitext(item)[1].lower() in supported_audio:
                    mod_time = os.path.getmtime(path + os.sep + item)
                    the_time = time.time()
                    if (int(the_time) - int(mod_time)) > 0: # check if file is still being copied
                        songs.append(item)
                elif os.path.splitext(item)[1].lower() in supported_imgs:
                    img = item
                else:
                    pass
            if len(songs) > 0: # checks if any actual songs found
                song_list.append((path, songs, img))
    if len(song_list) == 0:
        logger.info("[Import] No songs found in imports!")
        return False
    else:
        logger.info("[Import] Found songs!")
        return song_list

def cleanEmptyDirs():
    '''
    checks for supported songs in import_dir
    if no soungs found -> delete all files and dirs
    returns list of songs found
    '''
    songs = []
    file_paths = []  # List which will store all of the full filepaths.
    dir_paths = []

    for root, dirs, files in os.walk(import_dir):
        for file_name in files: # get list of all file paths
            file_path = os.path.join(root, file_name)
            file_paths.append(file_path)  # Add it to the list.

        for dir_name in dirs: # list all dir paths
            dir_path = os.path.join(root, dir_name)
            if getParent(dir_path) == 'import':
                dir_paths.append(dir_path)

    for file in file_paths: # check for supported song files
        if os.path.splitext(file)[1].lower() in supported_audio:
            logger.info("[Found] song: " + str(os.path.split(file)[1].lower()))
            songs.append(file)

    if len(songs) == 0: # if no songs found, fire sale everything
        for file in file_paths:
            file_name = os.path.split(file)[1]
            logger.info("[Deleting] file: " + str(file))
            if os.path.exists(extras_dir + file_name) == False:
                copy2((file), (extras_dir + file_name))
                logger.info("\t[Copied] File: " + str(file_name) + " to extras")
            os.remove(file)

        for dirs in dir_paths:
            logger.info("[Deleting] dir: " + str(dirs))
            rmtree(dirs)
    logger.info("[Import] Processed imports")
    return songs

def updateFileTag(file_path, tag_dict):
    f = taglib.File(file_path)
    for k, v in tag_dict.items():
        if k == 'year':
            k = 'DATE'
        if k == 'track':
            k = 'TRACKNUMBER'
        if len(v) > 0:
            f.tags[k.upper()] = [v]
        else:
            f.tags[k.upper()] = v
    try:
        updated_tag = f.save()
        logger.info("[Updated]: " + str(file_path))
        return True
    except IOError as e:
        logger.info("ERROR: updating " + str(file_path) + str(e.args))
        pass
    return False

def moveToLibrary(file_path):
    '''Renames and copies file to artist folder'''
    tag_dict = getFileTag(file_path)
    artist = tag_dict.get('artist')
    title = tag_dict.get('title')

    artist_dir = getArtistDir(artist)
    file_name = str(artist) + '_' + str(title)
    file_name = getValidFileName(file_name)
    file_ext = os.path.splitext(file_path)[1].lower()

    dup_count = 1
    while os.path.exists(artist_dir + file_name + file_ext) == True:
        file_name = artist + '_' + title + str(dup_count)
        dup_count += 1
    copy2((file_path), os.path.normpath(library_dir + artist_dir + file_name + file_ext))
    logger.info("[Moved] to library: " + str(file_path) + ". New name: " + str(file_name))
    return (file_name + file_ext)

def moveToUnsorted(file_path):
    '''Moves untitled files to root dir'''
    file_name = os.path.split(file_path)[1]
    file_set = os.path.splitext(file_name)
    file_name = getValidFileName(file_set[0])
    new_name = file_name
    file_ext = os.path.splitext(file_path)[1].lower()

    dup_count = 1
    while os.path.exists(root_dir + new_name + file_ext) == True:
        new_name = file_name + str(dup_count)
        dup_count += 1
    copy2((file_path), (root_dir + new_name + file_ext))
    logger.info("[Moved] to unsorted: " + str(file_path) + ". New name: " + str(new_name))
    return (new_name + file_ext)

def moveToDuplicates(file_path):
    file_name = os.path.split(file_path)[1]
    file_set = os.path.splitext(file_name)
    file_name = getValidFileName(file_set[0])
    file_ext = file_set[1]
    copy2((file_path), (dup_dir + file_name + file_ext))
    logger.info("[Moved] to duplicates: " + str(file_path) + ". New name: " + str(file_name))

def removeImportedFile(file_path):
    os.remove(file_path)

def ripArt(file_path):
    if os.path.splitext(file_path)[1] == '.mp3':
        try:
            audiofile = eyed3.load(file_path)
            eyed3_tag = audiofile.tag
            image = eyed3_tag.images[0].image_data
            name = getValidFileName(eyed3_tag.album).replace(" ", "")
            dup_count = 1
            while os.path.exists(art_dir + name + '.jpg') == True:
                with open(art_dir + name + '.jpg', 'rb') as found:
                    if found.read() == image:
                        return str(name) + '.jpg'
                name = eyed3_tag.album + str(dup_count)
                dup_count += 1
            with open(art_dir + name + '.jpg', 'wb') as f:
                f.write(image)
                logger.info("[Image] created: " + str(name))
            return str(name) + '.jpg'
        except:
            logger.info("[Image] could not be found")
            return False
    else:
        return False

def manageUpdate():
    import_list = checkImports()
    for folder_set in import_list:
        songs = folder_set[1]
        path = folder_set[0]
        if len(songs) == 0:
            logger.info("[Manage] No songs found!")
        else:
            logger.info("[Manage] Songs found!")
        for song in songs:
            logger.info("[Manage] Sorting " + str(song))
            file_path = os.path.join(path + song)
            file_hash = newHash(file_path)
            found_hash = findHashInDB(file_hash)
            if not found_hash:
                song_tag = getFileTag(file_path)
                artist = song_tag.get('artist')
                title = song_tag.get('title')
                if artist and title:
                    new_path = library_dir + getArtistDir(artist) + moveToLibrary(file_path)
                    removeImportedFile(file_path)
                    db_tag = createDBEntry(new_path)
                    addID(db_tag[0], db_tag[1])
                    addArtistToSet(artist)
                else:
                    artist_title = guessArtistTitleFromTitle(song)
                    artist = artist_title[0]
                    title = artist_title[1]
                    if artist and title:
                        new_path = root_dir + moveToUnsorted(file_path)
                        removeImportedFile(file_path)
                        db_tag = createDBEntry(new_path)
                        tag_dict = db_tag[1]
                        addID(db_tag[0], db_tag[1])
                        if updateFileTag(new_path, {"artist":artist, "title":title}):
                            logger.info("[Manage] renaming: " + str(song))
                            unsorted_path = new_path
                            new_path = library_dir + getArtistDir(getValidFileName(artist)) + moveToLibrary(new_path)
                            updateID(db_tag[0], {"artist":artist_title[0], "title":artist_title[1], 'uid':newHash(new_path), 'file':(os.path.split(new_path)[1]), 'sorted':True})
                            removeImportedFile(unsorted_path)
                            addArtistToSet(artist)
                        else:
                            logger.info("ERROR: Could not update tags")

                    else:
                        new_path = root_dir + moveToUnsorted(file_path)
                        removeImportedFile(file_path)
                        db_tag = createDBEntry(new_path)
                        addID(db_tag[0], db_tag[1])
            else:
                moveToDuplicates(file_path)
                addToDuplicateList(file_path, found_hash)
                removeImportedFile(file_path)
    logger.info("[Manage] Pushing update to DB...")
    buildDB(db_organizer)

#====================================================================================================================================================
#=======================================================================GETTERS======================================================================
#====================================================================================================================================================

def findHashInDB(file_hash):
    ids = db_organizer.get('ids')
    if len(ids) > 0:
        for item in ids:
            uids = ids[item]['uid']
            for uid in uids.keys():
                if file_hash == uid:
                    return ids[item]['file']
    return False

def getFileTag(file_path):
    logger.info("[GET] file tag: " + str(file_path))
    tag_dict = {}
    f = taglib.File(file_path)
    for k, v in f.tags.items():
        if k == 'DATE':
            k = 'year'
        if k == 'TRACKNUMBER':
            k = 'track'
        if k.lower() in fields:
            if len(v) > 0:
                tag_dict[k.lower()] = v[0]
            else:
                tag_dict[k.lower()] = v
    tag_dict['img'] = ripArt(file_path)
    tag_dict['length'] = str(f.length // 60) + ":" + str(f.length % 60).zfill(2)
    tag_dict['bitrate'] = f.bitrate
    tag_dict['size'] = os.path.getsize(file_path)
    artist_title = cleanArtistTitle(tag_dict.get('artist'), tag_dict.get('title'))
    if tag_dict.get('artist'):
        tag_dict['artist'] = artist_title[0]
    if tag_dict.get('title'):
        tag_dict['title'] = artist_title[1]
    if tag_dict.get('track'):
        tag_dict['track'] = cleanTrack(tag_dict.get('track'))
    if tag_dict.get('year'):
        if len(tag_dict.get('year')) > 4:
            tag_dict['year'] = tag_dict['year'][:4]
    logger.info("got")
    return tag_dict

def getDBTag(song_id):
    ids = db_organizer.get('ids')
    if ids.get(str(song_id)):
        return ids.get(str(song_id))
    else:
        logger.info("ERROR: getDBTag: id not found")
        return False

def isSorted(song_id):
    ids = db_organizer.get('ids')
    if ids.get(str(song_id))['sorted'] == True:
        return True
    else:
        return False

def getParent(file_path):
    source = os.path.split(file_path)[0]
    parent = os.path.split(source)[1]
    return parent

def getParentPath(file_path):
    source = os.path.split(file_path)[0] + os.sep
    return source

def getArtistDir(artist):
    if artist[0].isalpha():
        first_let = artist[0].lower()
    elif artist[0].isnumeric():
        first_let = '0'
    elif artist[1].isalpha():
        first_let = artist[1].lower()
    elif artist[1].isnumeric():
        first_let = '0'
    elif artist[2].isalpha():
        first_let = artist[2].lower()
    elif artist[2].isnumeric():
        first_let = '0'
    elif artist[3].isalpha():
        first_let = artist[3].lower()
    elif artist[3].isnumeric():
        first_let = '0'
    elif artist[4].isalpha():
        first_let = artist[4].lower()
    elif artist[4].isnumeric():
        first_let = '0'
    elif artist[5].isalpha():
        first_let = artist[5].lower()
    elif artist[5].isnumeric():
        first_let = '0'
    else:
        first_let = '0'
    artist_dir = first_let + os.sep
    return artist_dir

def getAllIDs():
    all_ids = []
    ids = db_organizer.get('ids')
    for num in ids:
        all_ids.append(num)
    return all_ids

def getSortedIDs():
    sorted_ids = []
    ids = db_organizer.get('ids')
    if len(ids) > 0:
        for num in ids:
            if ids[num].get('sorted') == True:
                sorted_ids.append(num)
    return sorted_ids

def getUnsortedIDs():
    unsorted_ids = []
    ids = db_organizer.get('ids')
    if len(ids) > 0:
        for num in ids:
            if ids[num].get('sorted') == False:
                unsorted_ids.append(num)
    return unsorted_ids

def getArtistSet():
    artists = sorted(db_organizer.get('artists'), key=lambda item: (int(item.partition(' ')[0])
                                                                    if item.isdigit() else float('inf'), item))

    return artists

def getDuplicatesWIntegrity():
    #return list in duplicates folder that matches db list
    pass

#====================================================================================================================================================
#=======================================================================SORTING======================================================================
#====================================================================================================================================================

def sortByArtist(ids_list):
    all_ids = db_organizer.get('ids')
    ids_to_sort = {}
    unsorted = []
    for song_id in ids_list:
        if all_ids[song_id].get('sorted'):
            ids_to_sort[song_id] = all_ids[song_id]
        else:
            unsorted.append(song_id)
    ids_to_sort = sorted(ids_to_sort.items(), key=lambda x: (x[1].get('artist'), str(x[1].get('album')), str(x[1].get('track'))))
    ids_sorted = []
    for num in ids_to_sort:
        ids_sorted.append(num[0])
    for num in unsorted:
        ids_sorted.append(num)
    return ids_sorted


def searchSongs(arg):
    ids = db_organizer.get('ids')
    terms = set()
    for num, tag in ids.items():
        for term, data in tag.items():
            if term in fields_mod and data != None:
                if str(arg).lower() in str(data).strip().lower():
                     terms.add(num)
    return list(terms)

def getRecent():
    ids = db_organizer.get('ids')
    last_id = db_organizer.get('last_id')
    terms = set()
    for num in ids.keys():
        if (last_id - int(num)) < 251:
            terms.add(num)
    return sorted(list(terms), reverse=True)

#====================================================================================================================================================
#=======================================================================FORMATTING===================================================================
#====================================================================================================================================================

def remove_non_ascii(text):
    return bytes.decode(unicodedata.normalize('NFKD',str(text)).encode("ascii","ignore"))

def cleanTagDict(tag_dict):
    '''Returns only fields in [fields]'''
    clean_dict = {}
    for field in fields:
        if tag_dict.get(field):
            clean_dict[field] = tag_dict.get(field)
    return clean_dict

def libraryTags(tag_dict):
    '''Returns only fields in [fields_lib]'''
    clean_dict = {}
    for field in fields_lib:
        if tag_dict.get(field):
            clean_dict[field] = tag_dict.get(field)
    return clean_dict

def json2client(ids):
    js = "{"
    for song_id in ids:
        js += "\n\t\"" + song_id + "\":\"" + ids[song_id]["file"] + "\",\n"
    js = js[:-2] +  "\n}"
    return js

def json2list(id_list):
    ids = db_organizer['ids']
    js = "{"
    for song_id in id_list:
        js += "\n\t\"_" + song_id + "\": {\n"
        tags = libraryTags((ids[song_id]))
        for tag, value in tags.items():
            js += "\t\t\"" + tag + "\": \"" + str(value) + "\",\n"
        js = js[:-2] + "\n\t},\n"
    js = js[:-2] +  "\n}"
    return js

def cleanArtistTitle(artist, title):
    '''Reformats (feat. ) and [prod ] tags for titles'''
    logger.info("Cleaning artist/title: " + str(artist) + " _ " + str(title))
    if title != None:
        title = remove_non_ascii(title)
        title = title.replace(" / ", ", ")
        title = title.replace("/", ", ")
        title = title.replace("ft.", "feat.")
        title = title.replace("ft:", "feat.")
        title = title.replace("Ft.", "feat.")
        title = title.replace(" ft ", "feat. ")
        title = title.replace("Feat.", "feat.")
        title = title.replace("feat:", "feat.")
        title = title.replace("Feat:", "feat.")
        title = title.replace("Featuring", "feat.")
        title = title.replace("featuring", "feat.")
        title = title.replace("(ft", "(feat.")
        title = title.replace("Ft", "feat.")
        title = title.replace("Feat", "feat.")
        datpiff = title.find("DatPiff Exclusive")
        if datpiff > 0:
            if len(title) != datpiff + 18:
                title = title[:(datpiff -1)] + title[(datpiff + 18)]
            else:
                title = title[:(datpiff -1)]
            title = title.strip()
        feat_start = title.find('feat')
        if feat_start > 0 and feat_start != (len(title) -1):
            if title[(feat_start -1)] != "(":
                feature = title[feat_start:]
                title = title[:feat_start] + "(" + feature + ")"
            op_count = title.count("(")
            cl_count = title.count(")")
            if op_count > cl_count:
                title += ")"

        title = title.strip()

    if artist != None:
        artist = remove_non_ascii(artist)
        artist = artist.replace(" / ", ", ")
        artist = artist.replace("/", ", ")
        artist = artist.replace("ft.", "feat.")
        artist = artist.replace("Ft.", "feat.")
        artist = artist.replace ("Ft:", "feat.")
        artist = artist.replace("Feat.", "feat.")
        artist = artist.replace("ft", "feat.")
        artist = artist.replace("Ft", "feat.")
        artist = artist.replace("Feat", "feat.")
        feat_start = artist.find('feat')
        if feat_start > 0:
            if artist[(feat_start -1)] != "(":
                artist = artist[:feat_start] + "(" + artist[feat_start:] + ")"
        if artist[:4].lower() == "the ":
            artist = artist[4:] + ", The"
        artist = artist.strip()

    if artist != None and title != None:
        feat_artist = artist.find('feat')
        if feat_artist > 0:
            title += " (" + artist[feat_artist:]
            op_count = artist.count("(")
            cl_count = artist.count(")")
            if op_count > cl_count:
                title += ")"
            artist = artist[:(feat_artist - 2)]
            artist = artist.strip()

        if title.find(artist) == 0:
            title = title[len(artist):]
            title = title.strip()
            index = 0
            for char in title:
                if char.isalnum():
                    break
                index += 1
            title = title[index:]

    if title != None:
        prod_start = title.lower().find('prod.')
        if prod_start == -1:
            prod_start = title.lower().find('prod ')
        if prod_start > 0:
            if title[(prod_start -1)] != "[":
                step = 1
                if title[(prod_start -2)] == " ":
                    step = 2
                if title[(prod_start -1)] == "(":
                    end_para = title[prod_start:].find(")") + prod_start
                    if end_para > prod_start:
                        if end_para != (len(title) -1):
                            title = title[:(prod_start -step)] + title[(end_para +1):] + " [" + title[prod_start:(end_para)] + "]"
                        else:
                            title = title[:(prod_start -step)] + " [" + title[prod_start:(end_para)] + "]"
                    else:
                        title = title[:(prod_start -step)] + " [" + title[prod_start:] + "]"
                else:
                    end_para = title.find(")")
                    if end_para > 0:
                        title = title[:(prod_start -step)] + ")" + " [" + title[prod_start:(end_para)] + "]"
                    else:
                        title = title[:(prod_start -step)] + " [" + title[prod_start:] + "]"
            else:
                step = 1
                if title[(prod_start -2)] == " ":
                    step = 2
                end_bracket = title[prod_start:].find("]") + prod_start
                if end_bracket > prod_start:
                    if end_bracket != (len(title) -1):
                        title = title[:(prod_start -step)] + title[(end_bracket + 1):] + " [" + title[prod_start:end_bracket] + "]"
                    else:
                        title = title[:(prod_start -step)] + " [" + title[prod_start:]
                else:
                    title = title[:(prod_start -step)] + " [" + title[prod_start:] + "]"

        title = title.strip()
    logger.info("Finished: " + str(artist) + " _ " + str(title))
    return artist, title

def guessArtistTitleFromTitle(filename):
    '''Finds Artist - Title in filename if any'''
    logger.info("Guessing artist/title: " + str(filename))
    filename = os.path.splitext(filename)[0]
    artist = None
    title = None
    artist_title = filename.split("-")
    elems = len(artist_title)
    if elems > 2:
        try:
            int(artist_title[0].strip())
            artist = artist_title[1].strip()
            title = artist_title[2].strip()
        except:
            try:
                int(artist_title[(elems-1)].strip())
                artist = artist_title[0].strip()
                title = artist_title[1].strip()
            except:
                artist = artist_title[0].strip()
                title = artist_title[1].strip()

    elif elems > 1:
        try:
            int(artist_title[1].strip())
        except:
            try:
                int(artist_title[0].strip())
            except:
                artist = artist_title[0].strip()
                title = artist_title[1].strip()
    cleaned_names = cleanArtistTitle(artist, title)
    logger.info("Finished: " + str(cleaned_names))
    return cleaned_names[0], cleaned_names[1]

def cleanTrack(track_num):
    '''Converts track numbers to ## format'''
    if len(str(track_num)) > 2:
        track_num = track_num.split("/")[0].zfill(2)
    else:
        track_num = track_num.zfill(2)
    return track_num

def cleanTags(tag_dict):
    '''Sanitizes fields
    -remove_non_ascii
    -cleanTrack
    -cleanArtistTitle
    '''
    for k in tag_dict.keys():
        if (type(tag_dict[k]) == type("")):
            tag_dict[k] = tag_dict[k].replace("\"", "'")
            tag_dict[k] = tag_dict[k].replace("\\", "")
            tag_dict[k] = remove_non_ascii(tag_dict[k])
    artist_title = cleanArtistTitle(tag_dict.get('artist'), tag_dict.get("title"))
    if artist_title[0]:
        tag_dict['artist'] = artist_title[0]
    if artist_title[1]:
        tag_dict['title'] = artist_title[1]
    if tag_dict.get('track'):
        tag_dict['track'] = cleanTrack(tag_dict.get('track'))
    if tag_dict.get('year'):
        tag_dict['year'] = tag_dict.get('year')[:4]
    return tag_dict

def isSongLocked(song_id):
    song_lock = source_dir + str(song_id) + ".lock"
    if os.path.exists(song_lock) == False:
        return False
    else:
        return True

def lockSong(song_id):
    song_lock = source_dir + str(song_id) + ".lock"
    open(song_lock,'a').close()

def unlockSong(song_id):
    song_lock = source_dir + str(song_id) + ".lock"
    os.remove(song_lock)

def processUpdate(song_id, new_tags):
    new_tags = cleanTags(new_tags)
    logger.info("[Processing] update: " + str(song_id) + str(new_tags))
    old_tags = getDBTag(song_id)
    if old_tags['sorted']:
        old_file = library_dir + getArtistDir(old_tags['artist']) + old_tags['file']
    else:
        old_file = root_dir + old_tags['file']
    new_path = old_file
    if not isSongLocked(song_id):
        lockSong(song_id)
        updateFileTag(old_file, new_tags)
        if new_tags.get('title') and new_tags.get('artist'):
            old_artist = old_tags.get("artist")
            old_title = old_tags.get("title")
            new_title = new_tags.get("title")
            new_artist = new_tags.get("artist")
            if old_title != new_title or old_artist != new_artist:
                new_path = library_dir + getArtistDir(new_artist) + moveToLibrary(old_file)
                removeImportedFile(old_file)
                addArtistToSet(new_artist)
            if old_tags['sorted'] == False:
                new_tags['sorted'] = True
        else:
            new_tags['sorted'] = False
            new_path = root_dir + moveToUnsorted(old_file)
            removeImportedFile(old_file)
        new_tags['uid'] = newHash(new_path)
        new_tags['file'] = str(os.path.split(new_path)[1])
        updateID(song_id, new_tags)
        unlockSong(song_id)
        logger.info("[Success] updating")
    else:
        logger.info("ERROR: Song currently locked")
    return True
