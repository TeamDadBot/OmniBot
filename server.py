import serial
import struct
import time

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



ser = serial.Serial('COM5')  # open serial port
percentage = 10
buffer = bytes(2)
pct_struct = struct.pack('B', percentage)
buffer = tx_commands['driveForward'] + pct_struct
junk=0

while True:

    bytesToRead = ser.inWaiting()
    robotdata=ser.read(bytesToRead)
    
    if robotdata == b'\x01':
        
        userrequest=input('What is your favortie color')

        if userrequest.upper() == 'W':
            buffer = tx_commands['driveForward'] + pct_struct
        elif userrequest.upper() == 'A':
            buffer = tx_commands['driveLeft'] + pct_struct
        elif userrequest.upper() == 'S':
            buffer = tx_commands['driveReverse'] + pct_struct
        elif userrequest.upper() == 'D':
            buffer = tx_commands['driveRight'] + pct_struct
        else:
            buffer = junk + pct_struct
        robotdata=0

        ser.write(buffer)     # write a string
    
ser.close()             # close port