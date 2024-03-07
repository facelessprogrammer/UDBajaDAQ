# -*- coding: utf-8 -*-
"""
Created on Wed Feb  7 18:20:46 2024

@author: hogan
"""

import time
import serial
import pynmea2
import pandas as pd
import busio
import board
import digitalio
from adafruit_mma8451 import MMA8451
from adafruit_max31855 import MAX31855

# Initialization block for sensors and serial port for GPS
def initialize_sensors():
    switch = digitalio.DigitalInOut(board.D4)
    switch.direction = digitalio.Direction.INPUT

    led1 = digitalio.DigitalInOut(board.D20)
    led1.direction = digitalio.Direction.OUTPUT

    led2 = digitalio.DigitalInOut(board.D26)
    led2.direction = digitalio.Direction.OUTPUT

    i2c = busio.I2C(board.SCL, board.SDA)
    spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    cs = digitalio.DigitalInOut(board.D5)  # Adjust pin as per your connection

    accelerometer = MMA8451(i2c)
    temp_sensor = MAX31855(spi, cs)
    
    serial_port = '/dev/ttyUSB0'  # Adjust this based on your system setup.
    gps_ser = serial.Serial(serial_port, 4800, timeout=1)

    fuel_sensor = digitalio.DigitalInOut(board.D23)
    fuel_sensor.direction = digitalio.Direction.INPUT
    fuel_sensor.pull = digitalio.Pull.DOWN

    return switch, led1, led2, accelerometer, temp_sensor, gps_ser, fuel_sensor

# Function to parse GPS data sentences into usable information
def parse_gps_data(line):
    try:
        msg = pynmea2.parse(line)
        if isinstance(msg, pynmea2.types.talker.RMC) and msg.datetime:
            return {
                "Date": msg.datetime.strftime('%Y-%m-%d'),
                "Time": msg.datetime.strftime('%H:%M:%S'),
                "Latitude": msg.latitude,
                "Longitude": msg.longitude,
                "Speed (Knots)": msg.spd_over_grnd,
                "Heading": msg.true_course,
            }
    except Exception as e:
        print(f"Failed to parse GPS data: {e}")
    return None

# Initialize sensors and GPS serial connection
switch, led1, led2, accelerometer, temp_sensor, gps_ser, fuel_sensor = initialize_sensors()

# Define loop control variables
loop = True
loop_counter = 0

while loop:
    data_points = []  # Reset data_points for each new run
    
    tot_cnt = 0  # Total count for the flow sensor.
    constant = 0.006  # This constant will be used to calculate L/min based on pulse count.

    led1.value = True

    try:

        while switch.value:  # Continuous data collection loop
            print("Collecting data...")

            line = gps_ser.readline().decode('ascii', errors='ignore').strip()
            gps_data = parse_gps_data(line) if line.startswith('$') else None
            
            rate_cnt = 0
            io_last = not fuel_sensor.value
            
            start_time = time.time()
            
            while time.time() - start_time <= 1:  # Measuring pulses per second.
                io_cur = fuel_sensor.value
                
                if io_cur != io_last:
                    rate_cnt += 1
                
                io_last = io_cur
                
            tot_cnt += rate_cnt
            
            LperM = round(rate_cnt * constant, 4)
            TotLit = round(tot_cnt * constant, 4)
            
            if gps_data:  # Ensure GPS data was successfully parsed before collecting more data.
                x_acc, y_acc, z_acc = accelerometer.acceleration  # Accelerometer readings.
                temp_celsius = temp_sensor.temperature 
                temp_fahrenheit = temp_celsius*9/5+32
                
                record = {**gps_data,
                    "X Acceleration": x_acc,
                    "Y Acceleration": y_acc,
                    "Z Acceleration": z_acc,
                    "MAX31855 Temperature (C)": temp_celsius,
                    "MAX31855 Temperature (F)": temp_fahrenheit,
                    "Fuel Rate (L/M)": LperM,
                    "Total Fuel (L)": TotLit}
                
                led2.value = True

                data_points.append(record)

        led2.value = False

                
    except (OSError, RuntimeError) as error:
        print(f"Error encountered: {error}")
        time.sleep(1.0)
        loop_counter += 1
        led2.value = False
        loop = True
        
    except KeyboardInterrupt:
        user_decision = input("Do you want to restart data collection? [y/n]: ")
        led2.value = False
        if user_decision.lower() == 'y':
            loop = True
            loop_counter += 1
        else:
            loop = False
            print("Exiting data collection.")
            led1.value = False
            
    finally:
        if data_points:
            df = pd.DataFrame(data_points)
            filename = 'data_final{}.csv'.format(loop_counter)
            df.to_csv(filename,index=False)
            print(f"Data successfully saved to '{filename}'.")