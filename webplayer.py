import gevent
from gevent import monkey
monkey.patch_all()
from bottle import request, template, static_file, abort, Bottle, debug, TEMPLATE_PATH
import errno
from gevent import sleep
from gevent.pywsgi import WSGIServer
from gevent.lock import Semaphore
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket import WebSocketError
from werkzeug.serving import run_with_reloader
from werkzeug.debug import DebuggedApplication
import subprocess
from musicdb2 import *

app = Bottle()
debug(True)
TEMPLATE_PATH[:] = [source_dir]

#======================================================================================================================================================
#=======================================================================FUNCTIONS======================================================================
#======================================================================================================================================================

def removeLibrarySongs():
    letter_dir = os.listdir(library_dir)
    songlist = []
    for folder in letter_dir:
        letter_songs = os.listdir(library_dir + folder)
        for song in letter_songs:
            songlist.append(folder + os.sep + song)
            os.remove(library_dir + folder + os.sep + song)
    return songlist

#====================================================================================================================================================
#=======================================================================ROUTING======================================================================
#====================================================================================================================================================

@app.route('/')
def hello():
    buildEmptyDB()
    cleanEmptyDirs()
    return removeLibrarySongs()

@app.route('/update')
def update():
    renewDB()
    if not checkImports():
        return "Cleared extra files"
    else:
        manageUpdate()
    return "Files imported"

@app.route('/static/:path#.+#', name='static') #load all files from /static/
def static(path):
    return static_file(path, root=root_dir) #passes music dir as /static/ easy access hack

@app.route('/download/<filename:path>')
def download(filename):
    return static_file(filename, root=root_dir, download=True)

@app.route('/music')
def musiclist():
    tplreturn = template('index')
    return tplreturn

@app.route('/websocket')
def handle_websocket():
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')
    while True:
        try:
            message = wsock.receive()
            if message:
                if message[:4] == "sear":
                    listids = ""
                    if message[4:] == "":
                        print('recent')
                        listids = json2list(getRecent())
                    else:
                        listids = json2list(sortByArtist(searchSongs(message[4:])))
                    wsock.send(listids)
                if message[:4] == "disp" or message[:4] == "tags":
                    wsock.send(json.dumps(getDBTag(message[4:])))
                if message[:4] == "upda":
                    user_tags = message[4:].split("^^^")
                    tag_dict = {}
                    tag_dict['id'] = user_tags[0]
                    tag_dict['title'] = user_tags[1]
                    tag_dict['artist'] = user_tags[2]
                    tag_dict['album'] = user_tags[3]
                    tag_dict['track'] = user_tags[4]
                    tag_dict['albumartist'] = user_tags[5]
                    tag_dict['year'] = user_tags[6]
                    tag_dict['genre'] = user_tags[7]
                    tag_dict = cleanTags(tag_dict)
                    song_id = tag_dict['id']
                    del tag_dict['id']
                    processUpdate(song_id, tag_dict)
                    wsock.send("hi")
                if message[:4] == "data":
                    wsock.send(json2client(renewDB()['ids']))
                wsock.close()
            else:
                listids = ""
                for num in sortByArtist(getRecent()):
                    listids += str(num) + ","
                wsock.send(listids[:-1])
                wsock.close()
        except WebSocketError:
            break

@app.route('/test')
def serve_test():
    return template('ws')

@run_with_reloader
def run_server():
    server = WSGIServer(("192.168.0.101", 8080), app, handler_class=WebSocketHandler)
    server.serve_forever()

run_server()
