#!/usr/bin/env python

import serial
import datetime

port="/dev/ttyUSB0"
baudrate=115200

logfile="can.log"

s = serial.Serial()

s.baudrate = baudrate
s.port = port

s.open()


try:
	while True:
		line = s.readline()
		line.strip()
		ds = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		print ds, line
		
		#Only open file momentarily, to deal with logrotate and stuff. 
		f = open(logfile, "a")
		f.write("%s %s" % (ds, line))
		f.close()
except:
	pass
finally:
	s.close()	
