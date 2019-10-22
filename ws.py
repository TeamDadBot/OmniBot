from fastapi import FastAPI
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocket
from starlette.staticfiles import StaticFiles
import serial
import struct
import math

# oh you fancy, huh?
# tx_commands =  {
#             'driveForward': b'\x10',
#             'driveReverse': b'\x11',
#             'driveLeft': b'\x12',
#             'driveRight': b'\x13',
#             'rotateLeft': b'\x14',
#             'rotateRight': b'\15',
#             'setDisabled': b'\20',
#             'setEnabled': b'\21',
#             }

app = FastAPI()
app.mount("/static", StaticFiles(directory='./static'),name='static')
ser = serial.Serial('/dev/ttyUSB0')  # open serial port

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Robot Control</title>
    </head>
    <body>
        <h1>Robot</h1>
        <input type="text" id="driveSpeed" autocomplete="off"/>
        <input type="text" id="driveDirection" autocomplete="off"/>
        <input type="text" id="driveSpin" autocomplete="off"/>
        <button onclick="send()">SEND IT!</button>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://192.168.1.100:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                messages.innerHTML = ""
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function send(event) {
                var speed = document.getElementById("driveSpeed")
                var direction = document.getElementById("driveDirection")
                var spin = document.getElementById("driveSpin")
                var command = ""
                command = command.concat(speed.value)
                command = command.concat(",")
                command = command.concat(direction.value)
                command = command.concat(",")
                command = command.concat(spin.value)
                ws.send(command)
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

html="""
<html>

	<head>

		<meta charset="utf-8">

		<meta name="viewport" content="width=device-width, user-scalable=no, minimum-scale=1.0, maximum-scale=1.0">

		

		<style>

		body {

			overflow	: hidden;

			padding		: 0;

			margin		: 0;

			background-color: #BBB;

		}

		#info {

			position	: absolute;

			top		: 0px;

			width		: 100%;

			padding		: 5px;

			text-align	: center;

		}

		#info a {

			color		: #66F;

			text-decoration	: none;

		}

		#info a:hover {

			text-decoration	: underline;

		}

		#container {

			width		: 100%;

			height		: 100%;

			overflow	: hidden;

			padding		: 0;

			margin		: 0;

			-webkit-user-select	: none;

			-moz-user-select	: none;

		}

		</style>

	</head>

	<body>

		<div id="container"></div>

		<div id="info">

			<a href="http://learningthreejs.com/blog/2011/12/26/let-s-make-a-3d-game-virtual-joystick/" target="_blank">VirtualJoystick.js</a>

			A library javascript to provide a virtual joystick on touchscreen.

			-

			inspired by this

			<a href="http://sebleedelisle.com/2011/04/multi-touch-game-controller-in-javascripthtml5-for-ipad/">post</a>

			from

			<a href="http://sebleedelisle.com/">seb.ly</a>

			<br/>

			Touch the screen and move

			-

			works with mouse too as debug

			<br/>

			<span id="result"></span>

		</div> 

		<script src="http://192.168.1.100:8000/static/virtualjoystick.js"></script>

		<script>

			console.log("touchscreen is", VirtualJoystick.touchScreenAvailable() ? "available" : "not available");

	
      var joystickangle = 0;
      var joystickmagnitude = 0;
	  var joystickspin = 0;
      var ws = new WebSocket("ws://192.168.1.100:8000/ws");

			var joystick	= new VirtualJoystick({

				container	: document.getElementById('container'),

				mouseSupport	: true,

        limitStickTravel: true,

			});

			var joystick2	= new VirtualJoystick({

				container	: document.getElementById('container'),

				strokeStyle	: 'orange',

				mouseSupport	: true,

        limitStickTravel: true,

			});

			joystick.addEventListener('touchStartValidation', function(event){
		var touch	= event.changedTouches[0];
		if( touch.pageX >= window.innerWidth/2 )	return false;
		return true
	});

			joystick2.addEventListener('touchStartValidation', function(event){
		var touch	= event.changedTouches[0];
		if( touch.pageX < window.innerWidth/2 )	return false;
		return true
	});

			joystick.addEventListener('touchStart', function(){

				console.log('down')

			})

			joystick.addEventListener('touchEnd', function(){

				console.log('up')

			})



			setInterval(function(){

        
        joystickmagnitude = Math.sqrt(Math.pow(joystick.deltaX(),2) + Math.pow(joystick.deltaY(),2));
        joystickmagnitude = joystickmagnitude/101;
        joystickangle = Math.atan2(joystick.deltaY(),joystick.deltaX());
		joystickspin = (joystick2.deltaX()/101 + 1 )/ 2.0;

        if (joystickangle <0){ 
          joystickangle = Math.abs(joystickangle);}
          else{
            joystickangle = Math.PI*2 - joystickangle;
		  }
		
		var spin = joystickspin;
		console.log('about to send command');
		var command='';
		command = command.concat(joystickmagnitude.toString());
		command = command.concat(',');
		command = command.concat(joystickangle.toString());
		command = command.concat(',');
		command = command.concat(spin.toString());
		console.log(command);
		ws.send(command);


				var outputEl	= document.getElementById('result');

				outputEl.innerHTML	= '<b>Result:</b> '

					+ ' dx:'+joystick.deltaX()

					+ ' dy:'+joystick.deltaY()

          + 'magnitude: ' + joystickmagnitude

          + 'angle: ' + joystickangle

					+ (joystick.right()	? ' right'	: '')

					+ (joystick.up()	? ' up'		: '')

					+ (joystick.left()	? ' left'	: '')

					+ (joystick.down()	? ' down' 	: '')	

			}, 1/30 * 1000);

		</script>

	</body>

</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global ser
    junk = 0
    await websocket.accept()
    await websocket.send_text("Enter something!")
    while True:
        bytesToRead = ser.inWaiting()
        robotdata=ser.read(bytesToRead)
        data = await websocket.receive_text()
        datas = data.split(',')
        if len(datas) != 3:
            print("you done messed up")
        speed = float(datas[0])
        direction = float(datas[1])
        spin = float(datas[2])
        speed = int(speed * 255)
        direction = int(direction * 255 / (2*math.pi))
        spin = int(spin*255)

        if robotdata == b'\x01':
            print('Speed = {speed} Direction = {direction} Spin = {spin}'.format(speed=speed, direction=direction, spin=spin))
            speed_byte = speed # this will be converted
            direction_byte = direction # this will be converted
            spin_byte = spin # this will be converted

            enabled = 1 # This needs to go to 0 if something goes haywire

            buffer = bytes(4)
            enabled_struct = struct.pack('B', enabled)
            speed_struct = struct.pack('B', speed_byte)
            direction_struct = struct.pack('B', direction_byte)
            spin_struct = struct.pack('B', spin_byte)

            buffer = enabled_struct + speed_struct + direction_struct + spin_struct

            robotdata=0

            ser.write(buffer) 
        
    ser.close()             # close port
