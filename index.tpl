<!DOCTYPE html>
<html lang="en-US">
	<head>
		<meta http-equiv="Content-type" content="text/html; charset=utf-8">
		<title>EliTunes</title>
		<link rel="stylesheet" href="/static/cfg/source/player.css" type="text/css" media="screen" />
	</head>

<body>
%from musicdb2 import *

<div id="liblink">
	<button class="lib_btn" onclick="clickCheck(this.id);">Most Recent</button>
</div>

<div id="artistscrollboxhide">
	<div id="letterlist">
		%for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZ#":
			<button class='letter_btn' onClick="scrollToLetter(this.innerText)">{{i}}</button>
			<br>
		%end
	</div>
	<div id="artists">
		%artists_set = getArtistSet()
		%for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
			<span id={{i}}></span>
			%for person in artists_set:
				%if str(person[:1].lower()) == str(i.lower()):
					<button class='artist_btn' onclick="clickCheck(this.textContent);">{{person}}</button>
					<br>
				%end
			%end
		%end
		<span id="#"></span>
		%for person in artists_set:
			%if person[0].isdigit():
				<button class='artist_btn' onclick="clickCheck(this.textContent);" >{{person}}</button>
				<br>
			%end
		%end
	</div>
</div>

<div id="nav">
	<div class="searchbox">
		<input type="text" name="Search" id="search" placeholder="Search library..." onkeyup="return delaySearch();">
	</div>
	<a id='youtubelink' href="https://www.youtube.com/results?search_query=" target="_blank">
		<img alt="YouTube" id="youtubebtn" src="/static/cfg/extras/assets/YouTube-logo-blue-arrow2.png">
	</a>
</div>

<div id="libscrollboxhide">
	<div id="lib">
		<div id="songlist">
			 <div class="loader"></div>
		</div>
	</div>
</div>
<div id="playlisthead">Playlist</div>
<div id="nowplayinghide">
	<div id="nowplaying">
		<h2 style="font-family:Lucida Console; text-align:center; font-style:italic;">Nothing Found</h2>
		<h3 style="font-family:Lucida Console; text-align:center; font-style:italic;">&#8592; Select a place to start</h3>
	</div>
</div>
	<div id="footer">
		<div id="controls">
			<button id="previous" onclick="playLast();">&#9194;</button>
			<button id="playpause" >&#9658;&#10073;&#10073</button>
			<button id="next" onclick="playNext();">&#9193;</button>
			<img src='/static/cfg/extras/assets/default-artwork.png' height="70" width="70" id="albumart" onclick="bounceart(this.src);">
		</div>
		<div id="scrobbler">
			<audio id="player"></audio>
			<div class="buffered">
				<span id="buffered-amount"></span>
			</div>
			<div class="progress" min="0" max="100" value="0">
				<span id="progress-amount"></span>
			</div>
			<figure id="progress-sphere"></figure>
			<div id='descriptor'>
					<span id='title'></span>
					<span>&emsp;</span>
					<span id='artist' onclick='clickCheck(this.textContent);'></span>
					<span>&nbsp;</span>
					<span id='album' onclick='clickCheck(this.textContent);'></span>
			</div>
			<div id='times'>
				<span id='progress-time'>0:00</span>
				<span>&#47;</span>
				<span id='time'>0:00</span>
			</div>
		</div>
		<input id='volume' type="range" min=0 max=1 step=0.01 value=1>
		<div id="version_info">{{version_info}}</div>
	</div>
<div id="bouncestage">
	<div id="travelart">
		<div id="bouncer">
			<div id="artafter"></div>
		</div>
	</div>
</div>
</body>
<script type="text/javascript" src="/static/cfg/source/player.js"></script>
</html>
