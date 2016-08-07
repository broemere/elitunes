
var typingTimer;
var doneTypingInterval = 700;
var musicdb = null;
var querylist = null;
var playlist = null;
var currenti = null;
var ws = null;
var player = document.getElementById('player');

function scrollToLetter(element_id){
    var element = document.getElementById(element_id);
    element.scrollIntoView({behavior:"smooth"});
}
function scrollIntoViewIfNeeded(target) {
    var rect = target.getBoundingClientRect();
    if (rect.bottom > window.innerHeight) {
        target.scrollIntoView({block: "end", behavior: "smooth"});
    }
    if (rect.top < 0) {
        target.scrollIntoView({behavior:"smooth"});
    }
}
function insertAfter(newNode, referenceNode) {
    referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling);
}
function clearUndefined(string){
    if (string == null){
        return "\u200b";
    }
    else {
        return string;
    }
}
function emptyUndefined(string){
    if (string == null){
        return "";
    }
    else {
        return string;
    }
}
function getArtistDir(filename){
    var regEx = /^[a-zA-Z\-]+$/;
        if (filename.substring(0,1).toLowerCase().match(regEx)) {
            return filename.substring(0,1).toLowerCase();
        }
        else {
            return '0';
    }
}
function start(){
    ws = new WebSocket("ws://192.168.0.101:8080/websocket");
}
function renewDB(){
    if(!ws || ws.readyState == 3)
        start();
    ws.send("data");
    ws.onopen = function() {};
    ws.onmessage = function (evt){
        musicdb = JSON.parse("[" +evt.data+ "]")[0];
        console.log("DB Received");
        ws.close();
    };
    ws.onclose = function () {
        start();
    };
}

function query(){
    if(!ws || ws.readyState == 3)
        start();
    ws.send("sear" + document.getElementById('search').value);
    ws.onopen = function() {};
    ws.onmessage = function (evt){
        console.log("Search received, clearing songlist");
        insertSongs(JSON.parse("[" +evt.data+ "]")[0]);
        ws.close();
    };
    ws.onclose = function () {
        start();
    };
}

function insertSongs(queryresults){
    var songlist = document.getElementById("songlist");
    var node = songlist;
    while (songlist.hasChildNodes()){
        if (node.hasChildNodes()){
            node = node.lastChild;
        }
        else {
            node = node.parentNode;
            node.removeChild(node.lastChild);
        }
    }
    querylist = Object.keys(queryresults);
    for (var id in queryresults) {
        if (queryresults.hasOwnProperty(id)) {
            var intd = id.slice(1);
            var songbtn = document.createElement("button");
            songbtn.setAttribute("id", id);
            songbtn.setAttribute("class", "btn");
            songbtn.setAttribute('onclick', "startPlaylist(" + intd + ");");
            songbtn.setAttribute('oncontextmenu', "showOps(this); return false;");
            var track = clearUndefined(queryresults[id].track);
            var title = queryresults[id].title;
            if (title == null) {
                title = musicdb[intd];
            }
            var length = clearUndefined(queryresults[id].length);
            var artist = clearUndefined(queryresults[id].artist);
            var album = clearUndefined(queryresults[id].album);
            var year = clearUndefined(queryresults[id].year);
            var bitrate = clearUndefined(queryresults[id].bitrate) + "k";
            var trackdiv = document.createElement("div");
            trackdiv.setAttribute("class", "track");
            if (track != "\u200b"){
                track = track.replace(/^0+/, "");
            }
            trackdiv.textContent = track;
            songbtn.appendChild(trackdiv);
            var titlediv = document.createElement("div");
            titlediv.setAttribute("class", "title");
            titlediv.textContent = title;
            songbtn.appendChild(titlediv);
            var lengthdiv = document.createElement("div");
            lengthdiv.setAttribute("class", "detail");
            lengthdiv.textContent = length;
            songbtn.appendChild(lengthdiv);
            var artistdiv = document.createElement("div");
            artistdiv.setAttribute("class", "artist");
            artistdiv.textContent = artist;
            songbtn.appendChild(artistdiv);
            var albumdiv = document.createElement("div");
            albumdiv.setAttribute("class", "album");
            albumdiv.textContent = album;
            songbtn.appendChild(albumdiv);
            var yeardiv = document.createElement("div");
            yeardiv.setAttribute("class", "detail");
            yeardiv.textContent = year;
            songbtn.appendChild(yeardiv);
            var bitdiv = document.createElement("div");
            bitdiv.setAttribute("class", "detail");
            bitdiv.textContent = bitrate;
            songbtn.appendChild(bitdiv);
            songlist.appendChild(songbtn);
        }
    }
}

function playSong(song_id) {
    var old_song = document.getElementById(playlist[currenti].slice(1));
    if (old_song){
        old_song.setAttribute('class', 'plbtn');
        old_song.children[0].textContent = currenti+1;
    }
    player.pause();
    currenti = playlist.indexOf("_"+song_id);
    var new_song = document.getElementById(song_id);
    new_song.setAttribute('class', 'cplbtn');
    new_song.children[0].innerHTML = "&#9658;";
    scrollIntoViewIfNeeded(new_song);
    player.src = "/static/library/" + getArtistDir(musicdb[song_id]) + "/" + musicdb[song_id];
    player.load();
    player.play();
    updateUI(song_id);
}

function playNext() {
    if (playlist) {
        if (currenti + 1 == playlist.length){
            playSong(playlist[0].slice(1));
        }
        else{
            playSong(playlist[currenti+1].slice(1));
        }
    }
}

function playLast() {
    if (playlist) {
        if (currenti == 0){
            playSong(playlist[0].slice(1));
        }
        else{
            playSong(playlist[currenti-1].slice(1));
        }
    }
}

function startPlaylist(song_id){
    var art = document.getElementById('bounceart');
    if (art){
        document.getElementById('bouncer').removeChild(art);
    }
    var nowplaying = document.getElementById('nowplaying');
    var starti = querylist.indexOf("_"+song_id);
    playlist = querylist.slice(starti);
    starti = 0;
    currenti = starti;
    var node = nowplaying;
    while (nowplaying.hasChildNodes()){
        if (node.hasChildNodes()){
            node = node.lastChild;
        }
        else {
            node = node.parentNode;
            node.removeChild(node.lastChild);
        }
    }
    for (var i=starti, len=playlist.length; i < len; i++) {
        var intd = playlist[i].slice(1);
        var songbtn = document.createElement("button");
        songbtn.setAttribute("id", intd);
        songbtn.setAttribute("class", "plbtn");
        songbtn.setAttribute('onclick', "playSong(" + intd + ");");
        /*songbtn.setAttribute('oncontextmenu', "showOps(this); return false;");*/
        var track = i+1-starti;
        var song_tags = document.getElementById(playlist[i]).children;
        var title = song_tags[1].textContent;
        var artist = song_tags[3].textContent;
        var trackdiv = document.createElement("div");
        trackdiv.setAttribute("class", "pltrack");
        trackdiv.textContent = track;
        songbtn.appendChild(trackdiv);
        var titlediv = document.createElement("div");
        titlediv.setAttribute("class", "pltitle");
        titlediv.textContent = title;
        songbtn.appendChild(titlediv);

        var artistdiv = document.createElement("div");
        artistdiv.setAttribute("class", "plartist");
        artistdiv.textContent = artist;
        songbtn.appendChild(artistdiv);

        nowplaying.appendChild(songbtn);
    }
    playSong(song_id);
}

function insertNext(song_id){
    if (playlist){
        var nowplaying = document.getElementById('nowplaying');
        playlist.splice(currenti+1, 0, "_"+song_id);
        var current_song = document.getElementById(playlist[currenti].slice(1));
        var songbtn = document.createElement("button");
        songbtn.setAttribute("id", song_id);
        songbtn.setAttribute("class", "plbtn");
        songbtn.setAttribute('onclick', "playSong(" + song_id + ");");
        /*songbtn.setAttribute('oncontextmenu', "showOps(this); return false;");*/
        var track = currenti+2;
        var song_tags = document.getElementById("_"+song_id).children;
        var title = song_tags[1].textContent;
        var artist = song_tags[3].textContent;
        var trackdiv = document.createElement("div");
        trackdiv.setAttribute("class", "pltrack");
        trackdiv.textContent = track;
        songbtn.appendChild(trackdiv);
        var titlediv = document.createElement("div");
        titlediv.setAttribute("class", "pltitle");
        titlediv.textContent = title;
        songbtn.appendChild(titlediv);

        var artistdiv = document.createElement("div");
        artistdiv.setAttribute("class", "plartist");
        artistdiv.textContent = artist;
        songbtn.appendChild(artistdiv);
        var songlist = nowplaying.children;
        for (var song in songlist){
            if (songlist.hasOwnProperty(song) && song > currenti) {
                songlist[song].children[0].textContent++;
            }
        }

        insertAfter(songbtn, current_song);
    }
}

function updateUI(id){
    if(!ws || ws.readyState == 3)
        start();
    ws.send("tags" + id);
    ws.onopen = function() {};
    ws.onmessage = function (evt){
        var tag = JSON.parse((evt.data));
        var title = tag.title;
        if (title == null){
            title = tag.file;
        }
        document.getElementById("title").textContent = title;
        document.getElementById("artist").textContent = tag.artist;
        document.getElementById("album").textContent = tag.album;
        var art_path = '/static/cfg/extras/albumart/';
        var image = null;
        image = tag.img;
        if (image) {
            document.getElementById("albumart").setAttribute('src', art_path + image);
        }
        else {
            document.getElementById("albumart").setAttribute('src', '/static/cfg/extras/assets/default-artwork.png');
        }
        document.getElementById("time").textContent = tag.length;
        ws.close();
    };
    ws.onclose = function () {
        start();
    };
}

function clickCheck(term){
    document.getElementById("search").value = term;
    document.getElementById('youtubelink').setAttribute('href', "https://www.youtube.com/results?search_query=" + term);
    console.log("Click search...");
    query();
}

function saveDetails(id) {
    var tag_table = document.getElementById('tag_table');
    var title = tag_table.rows[1].cells[0].textContent;
    var artist = tag_table.rows[1].cells[1].textContent;
    var album = tag_table.rows[1].cells[2].textContent;
    var track = tag_table.rows[1].cells[3].textContent;
    var albumartist = tag_table.rows[3].cells[1].textContent;
    var year = tag_table.rows[3].cells[2].textContent;
    var genre = tag_table.rows[3].cells[3].textContent;
    var artwork = tag_table.rows[5].cells[0].textContent;
    var format_tag = id + "^^^" + title + "^^^" + artist + "^^^" + album + "^^^" + track + "^^^" + albumartist + "^^^" + year + "^^^" + genre + "^^^" + artwork;

    if(!ws || ws.readyState == 3)
        start();
    ws.send("upda" + format_tag);
    document.getElementById("savebtn").innerHTML = "Updating...";
    ws.onopen = function() {};
    ws.onmessage = function (evt){
        musicdb = null;
        ws.close();
        console.log("Reloading DB...");
        checkIfSocketOpen = function()
        {
            if (ws.readyState == 1){
                renewDB();
                console.log("DB Reloaded!");
                clearInterval(loadInterval);
            }
        };
        var loadInterval = setInterval(checkIfSocketOpen, 100);

        checkIfDB = function()
        {
            if (musicdb != null && ws.readyState == 1){
                query();
                console.log("Query Reexicuted!");
                clearInterval(queryInterval);
            }
        };
        var queryInterval = setInterval(checkIfDB, 250);
    };
    ws.onclose = function () {
        start();
    };

}

var file_tag = null;
function showDetails(id) {
    var old_table = document.getElementById('tag_table');
    var closebtn = true;
    if (old_table){
        document.getElementById('detailsbtn').textContent = "Details...";
        closebtn = false;
        songlist.removeChild(old_table);
    }
    if (closebtn){
        document.getElementById('detailsbtn').textContent = "Close";
        var tag_table = document.createElement("table");
        tag_table.id = "tag_table";
        var head = tag_table.createTHead();
        var row1 = head.insertRow(0);
        var cell1 = row1.insertCell(0);
        cell1.innerHTML = "Title";
        var cell2 = row1.insertCell(1);
        cell2.innerHTML = "Artist";
        var cell3 = row1.insertCell(2);
        cell3.innerHTML = "Album";
        var cell4 = row1.insertCell(3);
        cell4.innerHTML = "Track";
        var row2 = tag_table.insertRow(1);
        row2.setAttribute('contentEditable', true);
        var cell5 = row2.insertCell(0);
        cell5.innerHTML = emptyUndefined(file_tag.title);
        var cell6 = row2.insertCell(1);
        cell6.innerHTML = emptyUndefined(file_tag.artist);
        var cell7 = row2.insertCell(2);
        cell7.innerHTML = emptyUndefined(file_tag.album);
        var cell8 = row2.insertCell(3);
        cell8.innerHTML = emptyUndefined(file_tag.track);

        var row3 = head.insertRow(2);
        var cell9 = row3.insertCell(0);
        cell9.innerHTML = "Length";
        var cell10 = row3.insertCell(1);
        cell10.innerHTML = "Album Artist";
        var cell11 = row3.insertCell(2);
        cell11.innerHTML = "Year";
        var cell12 = row3.insertCell(3);
        cell12.innerHTML = "Genre";
        var row4 = tag_table.insertRow(3);
        row4.setAttribute('contentEditable', true);
        var cell13 = row4.insertCell(0);
        cell13.innerHTML = file_tag.length;
        cell13.setAttribute('contentEditable', false);
        var cell14 = row4.insertCell(1);
        cell14.innerHTML = emptyUndefined(file_tag.albumartist);
        var cell15 = row4.insertCell(2);
        cell15.innerHTML = emptyUndefined(file_tag.year);
        var cell16 = row4.insertCell(3);
        cell16.innerHTML = emptyUndefined(file_tag.genre);

        var image = file_tag.img;
        if (image){
            var artcell = row1.insertCell(4);
            artcell.rowSpan = 0;
            artcell.innerHTML = "<img src='/static/cfg/extras/albumart/" + image + "' width=200 height=200>";
        }
        var row5 = head.insertRow(4);
        var cell17 = row5.insertCell(0);
        cell17.innerHTML = "Artwork";
        var row6 = head.insertRow(5);
        row6.setAttribute("contentEditable", true);
        var urlcell = row6.insertCell(0);
        urlcell.colSpan = 0;
        urlcell.innerHTML = "url";
        var row7 = head.insertRow(6);
        var cell18 = row7.insertCell(0);
        cell18.innerHTML = "<br><button id='savebtn' onclick='saveDetails(" + id + ");'>Update</button>";

        insertAfter(tag_table, ops_table);
        scrollIntoViewIfNeeded(tag_table);
    }
}
function showOps(song) {
    var songlist = document.getElementById("songlist");
    var id = song.id.slice(1);
    if(!ws || ws.readyState == 3)
        start();
    ws.send("tags" + id);
    ws.onopen = function() {};
    ws.onmessage = function (evt){
        var old_table = document.getElementById('tag_table');
        if (old_table){
            songlist.removeChild(old_table);
        }
        var old_ops = document.getElementById('ops_table');
        if (old_ops){
            songlist.removeChild(old_ops);
        }

        file_tag = JSON.parse(evt.data);
        var ops_table = document.createElement("table");
        ops_table.id = "ops_table";
        var ophead = ops_table.createTHead();
        var oprow = ophead.insertRow(0);
        var op1 = oprow.insertCell(0);
        op1.innerHTML = "<button id='detailsbtn' onclick='insertNext(" + id + ");'>Play Next</button>";
        var op2 = oprow.insertCell(1);
        var artist_dir = getArtistDir(file_tag.file);
        op2.innerHTML = "<a href='/download/library/" + artist_dir + "/" + file_tag.file + "'  target='_blank'>Download</a>";
        var op3 = oprow.insertCell(2);
        op3.innerHTML = "Lyrics";
        var op4 = oprow.insertCell(3);
        op4.innerHTML = "<button id='detailsbtn' onclick='showDetails(" + id + ");'>Details...</button>";
        insertAfter(ops_table, song);
        ws.close();
    };
    ws.onclose = function () {
        start();
    };
}

function bounceart(path) {
    var art = document.getElementById('bounceart');
    var bouncer = document.getElementById('bouncer');
    var artafter = document.getElementById('artafter');
    if (art){
        bouncer.removeChild(art);
    }
    else{
        art = document.createElement('img');
        art.setAttribute('id', 'bounceart');
        art.setAttribute('src', path);
        art.setAttribute('onclick', 'bounceart(this.src)');
        insertAfter(art, artafter);
    }
}
//Detect keystroke and only execute after the user has finish typing
function delaySearch()
{
    clearTimeout(typingTimer);
        typingTimer = setTimeout(
        function(){
            document.getElementById('youtubelink').setAttribute('href', "https://www.youtube.com/results?search_query=" + document.getElementById('search').value);
            console.log("Executing seach...");
            query();
        },
        doneTypingInterval
    );
    return true;
}

var progressBar = document.querySelector(".progress");
var volumeBar = document.getElementById('volume');
var playbtn = document.getElementById("playpause");

player.addEventListener('progress', function() {
    var bufferedEnd = player.buffered.end(0);
    var duration =  player.duration;
    if (duration > 0) {
        document.getElementById('buffered-amount').style.width = ((bufferedEnd / duration)*100) + "%";
    }
});

player.addEventListener('timeupdate', function() {
    var duration =  player.duration;
    if (duration > 0) {
        document.getElementById('progress-amount').style.width = ((player.currentTime / duration)*100) + "%";
        var numminutes = Math.floor((((player.currentTime % 31536000) % 86400) % 3600) / 60);
        var numseconds = Math.floor((((player.currentTime % 31536000) % 86400) % 3600) % 60);
        if (numseconds < 10) {
            numseconds = '0' + numseconds;
        }
        document.getElementById('progress-time').textContent = numminutes + ":" + numseconds;
    }
});

player.addEventListener('ended', function(){
    playNext();
});

progressBar.addEventListener("click", seek);
function seek(e) {
    var percent = e.offsetX / this.offsetWidth;
    player.currentTime = percent * player.duration;
    progressBar.value = percent * 100;
}


volumeBar.addEventListener("change", setVolume);
function setVolume() {
    player.volume = volumeBar.value;
}

playbtn.addEventListener("click", playPause);
function playPause() {
    player.paused ? player.play() : player.pause();
}

document.body.onkeyup = function(e){
    if(e.keyCode == 32){
        if ((document.activeElement.nodeName == 'INPUT' && document.activeElement.parentNode != document.getElementById('footer')) || (document.activeElement.isContentEditable === true)){}
        else {
            e.preventDefault();
            playPause();
        }
    }
    if (e.keyCode == 27){
        var art = document.getElementById('bounceart');
        if (art){
            document.getElementById('bouncer').removeChild(art);
        }
    }
    if (e.keyCode == 37){
        if ((document.activeElement.nodeName == 'INPUT' && document.activeElement.parentNode != document.getElementById('footer')) || (document.activeElement.isContentEditable === true)){}
        else{
            playLast();
        }
    }
    if (e.keyCode == 39){
        if ((document.activeElement.nodeName == 'INPUT' && document.activeElement.parentNode != document.getElementById('footer')) || (document.activeElement.isContentEditable === true)){}
        else{
            playNext();
        }
    }
};


document.addEventListener("DOMContentLoaded", function() {
    start();

    checkIfSocketOpen = function()
    {
        if (ws.readyState == 1){
            renewDB();
            clearInterval(loadInterval);
        }
    };
    var loadInterval = setInterval(checkIfSocketOpen, 100);

    checkIfDB = function()
    {
        if (musicdb != null && ws.readyState == 1){
            query();
            clearInterval(queryInterval);
        }
    };
    var queryInterval = setInterval(checkIfDB, 250);

});

window.onbeforeunload = function() {
    ws.onclose = function () {};
    ws.close();
    musicdb = null;
    playlist = null;
    ws = null;
    file_tag = null;

    return null;
};

window.addEventListener("beforeunload", function(e) {
    ws.onclose = function () {};
    ws.close();
    e.preventDefault();
    musicdb = null;
    playlist = null;
    ws = null;
    file_tag = null;

    return null;
}, false);
