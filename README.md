The purpoes of this document is to showcase the University of Dayton Baja Team's code for their Data Acquisition System

The imports are listed as:

import time  - Allows to have functionality in recording or delaying the current time

import serial  - Allows for communication to serial ports 

import pynmea2  - Libray for NMEA 0183 Protocol 

import pandas as pd  - Importing the Pandas package to use the 

import busio  - Busio moduel is imported to help support more serial protocals used in the code 

import board  - The board moduel is used to make constants on our pinout for the Raspberry Pi

import digitalio  - The digitalio module has classes giving access to low end digital IO

from adafruit_mma8451 import MMA8451  - This allows for the ability to read off the acceleration value from the MMA8451 board

from adafruit_max31855 import MAX31855  - This allows for the ability to read off the temperature in celsius value from the MAX31855. Then the simple conversion to Fahrenheit in the Python Code



Since the Raspberry Pi

