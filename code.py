# Metro IO demo
# Welcome to CircuitPython 2.2.0 :)

import board
import time
from digitalio import DigitalInOut, Direction, Pull
import pulseio
import math
import busio

#boolean to invert motors on left side of robot since they are mechanically mounted to spin opposite motors on right side
global invertleft = 1

tx_commands = {'request_values': b'\01'}

# oh you fancy, huh?
rx_commands =  {
            0x10: lambda robot, val: robot.driveForward(val),
            0x11: lambda robot, val: robot.driveReverse(val),
            0x12: lambda robot, val: robot.driveLeft(val),
            0x13: lambda robot, val: robot.driveRight(val),
            0x14: lambda robot, val: robot.rotateLeft(val),
            0x15: lambda robot, val: robot.rotateRight(val),
            0x20: lambda robot, val: robot.setDisabled(),
            0x21: lambda robot, val: robot.setEnabled(),
            }

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
        invertleft*math.sin(direction+math.pi()/4)+spin,
        #left rear
        invertleft*math.sin(direction-math.pi()/4)+spin,
        #right front
        math.sin(direction-math.pi()/4)-spin,
        #right rear
        math.sin(direction+math.pi()/4)-spin]


        biggestmotoroutput =  abs(max(motorspeeds,key=abs))

        #normalizing if the magnitude is over 1 (since motor speeds range from 0-1) and then applying the magnitude vector
        #this method may mess with expected spin speed but o well.
        if biggestmotoroutput>1:
            motorspeeds = x*(magnitude/biggestmotoroutput) for x in motorspeeds
        
        return motorspeeds


    def drive(self, motorspeeds):
        self.setDisabled()
        self.fl.setSpeed(motorspeeds[0])
        self.fr.setSpeed(motorspeeds[1])
        self.rl.setSpeed(motorspeeds[2])
        self.rr.setSpeed(motorspeeds[3])
        self.setEnabled()       


    



rear_left_motor = Motor(pin_dir = board.D2, enable = board.D3, pwm = board.D4)
rear_right_motor = Motor(pin_dir = board.D7, enable = board.D6, pwm = board.D5, motor_reversed = True)
front_right_motor = Motor(pin_dir = board.D9, enable = board.D8, pwm = board.D10)
front_left_motor = Motor(pin_dir = board.D12, enable = board.D13, pwm = board.D11, motor_reversed = True)
my_robot = Robot(front_left_motor, front_right_motor, rear_left_motor, rear_right_motor)
print("Setting up")

uart = busio.UART(board.TX, board.RX, baudrate=9600)

######################### MAIN LOOP ##############################
while True:
    # request value via serial
    tx_buf = tx_commands['request_values']
    uart.write(tx_buf)

    buf = bytearray(2)
    uart.readinto(buf, 2)
    command = buf[0]
    value = buf[1]
    value = value / 100
    print('Command: {0} Value: {1}'.format(command, value))

    if(command in rx_commands):
        rx_commands[command](my_robot, value)
    else:
        my_robot.setDisabled()

    #need to receive control vector over serial
    #vector = [magnitude, direction, spin]
    drive(calculatemotorspeeds(magnitude,direction,spin))

    time.sleep(1) # 10ms loop time
