from fastapi import FastAPI
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocket
import serial
import struct

# oh you fancy, huh?
tx_commands =  {
            'driveForward': b'\x10',
            'driveReverse': b'\x11',
            'driveLeft': b'\x12',
            'driveRight': b'\x13',
            'rotateLeft': b'\x14',
            'rotateRight': b'\15',
            'setDisabled': b'\20',
            'setEnabled': b'\21',
            }

app = FastAPI()
ser = serial.Serial('COM5')  # open serial port

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Robot Control</title>
    </head>
    <body>
        <h1>Robot</h1>
        <input type="text" id="driveSpeed" autocomplete="off"/>
        <button onclick="sendForward()">Forward</button>
        <button onclick="sendLeft()">Left</button>
        <button onclick="sendRight()">Right</button>
        <button onclick="sendReverse()">Reverse</button>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://192.168.4.1:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                messages.innerHTML = ""
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendForward(event) {
                var speed = document.getElementById("driveSpeed")
                var command = "Forward,"
                var command = command.concat(speed.value)
                ws.send(command)
                event.preventDefault()
            }
            function sendLeft(event) {
                var speed = document.getElementById("driveSpeed")
                var command = "Left,"
                var command = command.concat(speed.value)
                ws.send(command)
                event.preventDefault()
            }
            function sendRight(event) {
                var speed = document.getElementById("driveSpeed")
                var command = "Right,"
                var command = command.concat(speed.value)
                ws.send(command)
                event.preventDefault()
            }
            function sendReverse(event) {
                var speed = document.getElementById("driveSpeed")
                var command = "Reverse,"
                var command = command.concat(speed.value)
                ws.send(command)
                event.preventDefault()
            }
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
    
        if robotdata == b'\x01':
            await websocket.send_text("Press a command!")
            data = await websocket.receive_text()
            datas = data.split(',') # split on comma
            command = datas[0]
            speed = datas[1]

            buffer = bytes(2)
            speed_struct = struct.pack('B', speed)
        
            if command.upper() == 'FORWARD':
                buffer = tx_commands['driveForward'] + speed_struct
            elif command.upper() == 'LEFT':
                buffer = tx_commands['driveLeft'] + speed_struct
            elif command.upper() == 'RIGHT':
                buffer = tx_commands['driveReverse'] + speed_struct
            elif command.upper() == 'REVERSE':
                buffer = tx_commands['driveRight'] + speed_struct
            else:
                buffer = junk + speed_struct
            robotdata=0

            ser.write(buffer)     # write a string
        
    ser.close()             # close port