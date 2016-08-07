<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
<script>
        $(document).ready(function(){
            $("button").click(function(){
                var id = $(this).attr("id")
                var name = $(this).attr("name")
                document.getElementById('player').src = id;
                document.getElementById('player').play();
            });
        });
</script>
<!DOCTYPE html>
<html lang="en-US">
	<head>
		<meta http-equiv="Content-type" content="text/html; charset=utf-8">
		<title>EliTunes</title>
		<link rel="stylesheet" href="/static/cfg/player.css" type="text/css" media="screen" />
	</head>
    
	<body>
        
    <p>{{!myfiles}}{{!mp3dir}}</p>
%for i in myfiles:
%audiofile = mp3dir + i

<div>
    <button class='btn' id={{!audiofile}} name='edit'>{{!i}}</button>
    <br>
</div>
%end
        <audio controls id="player">
            <source src={{!audiofile}}>
        </audio>
        
        
    </body>
    
</html>
		
		
