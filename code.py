# Metro IO demo
# Welcome to CircuitPython 2.2.0 :)

import board
import time
from digitalio import DigitalInOut, Direction, Pull
import pulseio
import math
import busio

#boolean to invert motors on left side of robot since they are mechanically mounted to spin opposite motors on right side
invertleft = 1

tx_commands = {'request_values': b'\01'}

# oh you fancy, huh?
# rx_commands =  {
#             0x10: lambda robot, val: robot.driveForward(val),
#             0x11: lambda robot, val: robot.driveReverse(val),
#             0x12: lambda robot, val: robot.driveLeft(val),
#             0x13: lambda robot, val: robot.driveRight(val),
#             0x14: lambda robot, val: robot.rotateLeft(val),
#             0x15: lambda robot, val: robot.rotateRight(val),
#             0x20: lambda robot, val: robot.setDisabled(),
#             0x21: lambda robot, val: robot.setEnabled(),
#             }

class Motor:
    def __init__(self, pin_dir, enable, pwm, motor_reversed = False):
        self.pin_dir = pin_dir
        self.pin_enable = enable
        self.pin_pwm = pwm
        self.dir = DigitalInOut(pin_dir)
        self.dir.direction = Direction.OUTPUT
        self.enable = DigitalInOut(self.pin_enable)
        self.enable.direction = Direction.OUTPUT
        self.speed = pulseio.PWMOut(self.pin_pwm, frequency=5000, duty_cycle=0)
        self.enabled = False
        self.motor_reversed = motor_reversed

    def setEnable(self):
        if not self.enabled:
            self.enabled = True # Set internal state
            self.enable.value = True # Set the pin high to enable the motor

    def setDisable(self):
        if self.enabled:
            self.enabled = False # Set the internal state
            self.enable.value = False # Set the pin low to disable the motor
            self.setSpeed(0)

    def setSpeed(self, speed):
        if speed < 0.0: # Reverse Speed
            if self.motor_reversed:
                self.dir.value = False
            else:
                self.dir.value = True
            speed_value = math.floor(abs(speed) * 65535)
        elif speed > 0.0 and speed <= 1.00:
            if self.motor_reversed:
                self.dir.value = True
            else:
                self.dir.value = False
            speed_value = math.floor(abs(speed) * 65535)
        else:
            speed_value = 0
        self.speed.duty_cycle = speed_value # write the value to the motor

class Robot:
    def __init__(self, front_left_motor, front_right_motor, rear_left_motor, rear_right_motor):
        self.fl = front_left_motor
        self.fr = front_right_motor
        self.rl = rear_left_motor
        self.rr = rear_right_motor

    def setDisabled(self):
        #print('Call setDisabled')
        self.fl.setDisable()
        self.fr.setDisable()
        self.rl.setDisable()
        self.rr.setDisable()

    def setEnabled(self):
        #print('Call setEnabled')
        self.fl.setEnable()
        self.fr.setEnable()
        self.rl.setEnable()
        self.rr.setEnable()


    #calculating motor speed for mecanum drive
    #lots of help from these two sources
    #https://seamonsters-2605.github.io/archive/mecanum/
    #https://robotpy.readthedocs.io/projects/wpilib/en/latest/_modules/wpilib/drive/mecanumdrive.html#MecanumDrive.drivePolar
    #magnitude is speed of movement
    #direction is angle in radians off of x axis, counter-clockwise is positive
    #spin is the rotation rate (counter clockwise)
    def calculatemotorspeeds(self, magnitude, direction, spin):

        #need a function to check bounds if you are calling this from the main loop!!        
        global invertleft
        motorspeeds=[
        #left front
        math.sin(direction+math.pi/4)*magnitude+spin,
        #left rear
        math.sin(direction-math.pi/4)*magnitude+spin,
        #right front
        math.sin(direction-math.pi/4)*magnitude-spin,
        #right rear
        math.sin(direction+math.pi/4)*magnitude-spin]

        #motorspeeds = [x*magnitude for x in motorspeeds]


        biggestmotoroutput =  abs(max(motorspeeds,key=abs))
        print(biggestmotoroutput)

        #normalizing if the magnitude is over 1 (since motor speeds range from 0-1) and then applying the magnitude vector
        #this method may mess with expected spin speed but o well.
        if biggestmotoroutput>1:
            for i in range(0, len(motorspeeds)):
                motorspeeds[i] = motorspeeds[i]/biggestmotoroutput
        
        print(motorspeeds)
        
        return motorspeeds


    def drive(self, motorspeeds):
        self.setDisabled()
        self.fl.setSpeed(motorspeeds[2])
        self.fr.setSpeed(motorspeeds[0])
        self.rl.setSpeed(motorspeeds[1])
        self.rr.setSpeed(motorspeeds[3])
        self.setEnabled()       


    



rear_left_motor = Motor(pin_dir = board.D2, enable = board.D3, pwm = board.D4, motor_reversed=False)
rear_right_motor = Motor(pin_dir = board.D7, enable = board.D6, pwm = board.D5, motor_reversed = True)
front_right_motor = Motor(pin_dir = board.D9, enable = board.D8, pwm = board.D10, motor_reversed=False)
front_left_motor = Motor(pin_dir = board.D12, enable = board.D13, pwm = board.D11, motor_reversed = True)
my_robot = Robot(front_left_motor, front_right_motor, rear_left_motor, rear_right_motor)
print("Setting up")

uart = busio.UART(board.TX, board.RX, baudrate=9600)

######################### MAIN LOOP ##############################
while True:
    # request value via serial
    tx_buf = tx_commands['request_values']
    uart.write(tx_buf)

    buf = bytearray(4)
    uart.readinto(buf, 4)
    enabled = buf[0]
    magnitude_raw = buf[1]
    direction_raw = buf[2]
    spin_raw = buf[3]
    
    print('Enabled: {3} Raw Magnitude: {0} Raw Direction: {1} Raw Spin: {2}'.format(magnitude_raw, direction_raw, spin_raw, enabled))

    magnitude = magnitude_raw / 255.0 # magnitde_raw(0-255) -> magnitude(0-1)
    direction = direction_raw / 255.0 * 2*math.pi # direction_raw(0-255) -> direction(0-2pi radians)
    spin = (spin_raw - 127) / 127.0 # spin_raw(0-255) -> spin(0-1)

    print('Magnitude: {0} Direction: {1} Spin: {2}'.format(magnitude, direction, spin))

    if(enabled == 0):
        my_robot.setDisabled()
        my_robot.drive((0,0,0,0))
        print("DISABLED")
    else:
        my_robot.setEnabled()
        my_robot.drive(my_robot.calculatemotorspeeds(magnitude,direction,spin))
        print('Magnitude: {0} Direction: {1} Spin: {2}'.format(magnitude_raw, direction_raw, spin_raw))
    

    # my_robot.setDisabled...

    # This is the old code
    # command = buf[0]
    # value = buf[1]
    # value = value / 100
    # print('Command: {0} Value: {1}'.format(command, value))

    # if(command in rx_commands):
    #     rx_commands[command](my_robot, value)
    # else:
    #     my_robot.setDisabled()

    #need to receive control vector over serial
    #vector = [magnitude, direction, spin]


    time.sleep(1/60) # 10ms loop time
