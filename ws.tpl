<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/static/cfg/player.css" type="text/css" media="screen" />
    <script type="text/javascript">

        var typingTimer;
        var doneTypingInterval = 700;

        var ws = null;
        function start(){
            ws = new WebSocket("ws://192.168.0.101:8080/websocket");
        }
        function check(){
            if(!ws || ws.readyState == 3)
                start();
            ws.send(document.getElementById("search").value);
            ws.onopen = function() {
                console.log("Connected!");
            };
            ws.onmessage = function (evt){
                console.log(evt);
                console.log(evt.data);
                document.getElementById("url-displayname").textContent = "";
                document.getElementById("url-displayname").insertAdjacentHTML( 'afterbegin', evt.data );
                ws.close();
            };
            ws.onclose = function () {
                console.log("Closed!");
                check();
            };
        }

        //Detect keystroke and only execute after the user has finish typing
        function delayExecute()
        {
            clearTimeout(typingTimer);
                typingTimer = setTimeout(
                function(){
                    check();
                },
                doneTypingInterval
            );

            return true;
        }

        document.addEventListener("DOMContentLoaded", function() {
            start();
            //setInterval(check, 1000);
        });

        window.onbeforeunload = function() {
            ws.onclose = function () {};
            ws.close();
            return null;
        };

        window.addEventListener("beforeunload", function(e) {
            ws.onclose = function () {};
            e.returnValue = null;
            ws.close();
            return null;
        }, false);
        function playsong(songid) {
                var player = document.getElementById('player');
                player.pause();
                player.src = songid;
                player.load();
                player.play();
                return false;
        }
        function showStuff(btn, id) {
            var textbox = document.getElementById(id);
            var oldbox = document.getElementById("oldbox");
            if (oldbox != null) {
                oldbox.style.display = 'none';
                var newname = oldbox.name;
                oldbox.id = newname;
            }
            if (btn.name == 'song') {
                textbox.style.display = 'block';
                textbox.id = "oldbox";
                btn.name = 'songedit';
            }
            else {
                textbox.style.display = 'none';
                btn.name = 'song';
            }
            return false;
        }
  </script>
</head>
<body>
    <input type="text" name="Search" id="search" placeholder="Search library..." onkeyup="return delayExecute();">
    <p class="url">
    <div id="url-displayname">username</div>
  </p>
			<table id= >
				<tr>
					<th>Title</th>
					<th>Artist</th>
					<th>Album</th>
					<th>Track</th>
				</tr>
				<tr>
					<td>Photothot</td>
					<td>Joey Purp</td>
					<td>iiiDrops</td>
					<td>6</td>
				</tr>
				<tr>
					<th>Album Artist</th>
					<th>Year</th>
					<th>Genre</th>
					<th>Image</th>
				</tr>
				<tr>
					<td>Joey Purp</td>
					<td>2016</td>
					<td>Rap</td>
					<td></td>
				</tr>
			</table>
</body>
	<div id="footer">
	<audio controls id="player">
        <source src= >
    </audio>
</div>


</html>
