#!/usr/bin/env python3
#Written by Jared Blanchard
#Collects data from OPC-N2 and NOVA sensor simultaneously
    #~ NOVA
    #~ program to read data from Novafitness SDS101
    #~ http://aqicn.org/sensor/sds011/
    #~ Nils Jacob Berland
    #~ njberland@gmail.com / njberland@sensar.io
    #~ +47 40800410
    #~ The numbers produced are microgram pr m^3 of particles
	#~ OPC-N2
	#~ Originally from D.H.Hagan https://github.com/dhhagan


import serial
import os
import csv
import datetime
import time
import usbiss
import opc
import argparse
import sys

##### INITIATING THE OPC-N2 #####
try:
    time.sleep(5) #These sleeps helped for some reason
    #Open an SPI connection
    spi = usbiss.USBISS("/dev/ttyACM0", 'spi', spi_mode = 2, freq = 500000)
    time.sleep(5) #These sleeps helped for some reason
    alpha = opc.OPCN2(spi)
except Exception as e:
    print ("Startup Error: {}".format(e))
    sys.exit(1)
    
#Turn on the OPC
alpha.on()

#Wait for ten seconds to allow the sensor to boot up
time.sleep(10) #These sleeps helped for some reason

#change firmware to correct version   
alpha.firmware = {'major': 18, 'version': 18.2, 'minor': 2}

##### INITIATING THE NOVA #####

ser = serial.Serial('/dev/ttyUSB0', baudrate=9600, stopbits=1, parity="N",  timeout=2)

input("System Ready, press Enter to begin displaying data. Press ctrl+c to pause...")

##### STARTING THE DATA COLLECTION LOOP #####

status = "collecting"
while status == "collecting":
	
	
	##### PRINTING #####
	
	PM25 = 0 #initialize PM25 and PM10 for the NOVA sensor
	PM10 = 0
	OPC25 = 0
	OPC10 = 0
	counter = 0
	timestart = time.time()
	timer = 0
	try:
	    while True:
		    counter += 1
		    
		    ### OPC ###
		    
		    keys = ['Counter','Time']
		    data = [counter,time.time()-timestart]
		    #Read the histogram and print to console
		    #change histogram to show integer values instead of #/cc in bins
		    print("OPC")
		    for key, value in alpha.histogram(number_concentration = False).items():
		        #separated by commas
		        data.append(value)
		        keys.append(key)            
		        #print ("counter: {}\tKey: {}\tValue: {}".format(counter, key, value)) #This line prints all the data
		        if key == 'PM2.5':
		            OPC25=value
		        if key == 'PM10':
		            OPC10=value
		    print('PM2.5 - ',OPC25, 'PM10 - ', OPC10)#This line prints just PM2.5 and PM10 data
		    time.sleep(0.5)
		    
		    ### NOVA ###
		    
		    s = ser.read(1)
		    if ord(s) == int("AA",16):
		        s = ser.read(1)
		        if ord(s) == int("C0",16):
		            s = ser.read(7)
		            a = []
		            for i in s:
		                a.append(i)
		            #print(a)
		            pm2hb= s[0]
		            pm2lb= s[1]
		            pm10hb= s[2]
		            pm10lb= s[3]
		            cs = s[6]
		            timer = time.time() - timestart
		            PM25 = float(pm2hb + pm2lb*256)/10.0
		            PM10 = float(pm10hb + pm10lb*256)/10.0
		            datarow = [counter,timer,PM25,PM10]
		            # we should verify the checksum... it is the sum of bytes 1-6 truncated...
		            print("NOVA")
		
		            try:
		                print("PM2.5 - ", float(pm2hb + pm2lb*256)/10.0 ," PM10 - ", float(pm10hb + pm10lb*256)/10.0)
		            except:
		                pass
		    else:
		        pass   
	
	except KeyboardInterrupt:
	    pass
	
	

	
	choice = input("Paused... To start again, press 'y' then Enter, to quit, press only Enter")
	if choice == "y" or choice == "Y":
		status = "collecting"
	else:
		status = "finished"
		#Shut down the opc
		alpha.off()

#To do - for some reason, ctrl+c doesn't always shut the OPC off. I think it has to do with the timing.
#If I'm in the middle of communications, it won't work

"""
Other values that can be read from the OPC-N2
n = alpha.sn() #Serial Number
print(n)
alpha.read_firmware()
"""
