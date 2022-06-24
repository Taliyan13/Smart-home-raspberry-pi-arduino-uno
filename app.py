'''
	Raspberry Pi GPIO Status and Control
'''
import RPi.GPIO as GPIO
from flask import Flask, render_template, request
import serial
import json
import threading
import time

import datetime
from email.mime.text import MIMEText
import os
import smtplib


app = Flask(__name__)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#user+password mail
email = 'ruppin.smarthome@gmail.com'
email_password = 't13Y0893'
mutex = threading.Lock()


#define sensors GPIOs
button = 23

motorA = 27
motorB = 18
#define actuators GPIOs
ledRed = 17
ledYlw = 13
ledGrn = 26
#initialize GPIO status variables
buttonSts = 0
ledRedSts = 0
ledYlwSts = 0
ledGrnSts = 0

motorASts = 0
motorBSts = 0

tempSts=0
humiSts=0
waterSts=0
flameSts=0
soilSts=0
medicineMagnetSts=0



last_soil_moisture_value = 0 #temperature sensor
last_humidity_value = 0
last_water_value = 0
last_flame_value = 0
last_soil_value = 0 #soil sensor
last_medicineMagent_value = 0 #magnet for medicine check


# Define button and PIR sensor pins as an input
GPIO.setup(button, GPIO.IN)   
# Define led pins as output
GPIO.setup(ledRed, GPIO.OUT)   
GPIO.setup(ledYlw, GPIO.OUT) 
GPIO.setup(ledGrn, GPIO.OUT) 

GPIO.setup(motorA, GPIO.OUT) 
GPIO.setup(motorB, GPIO.OUT) 

# turn leds OFF 
GPIO.output(ledRed, GPIO.LOW)
GPIO.output(ledYlw, GPIO.LOW)
GPIO.output(ledGrn, GPIO.LOW)
	
@app.route("/")
def index():
	# Read GPIO Status
	buttonSts = GPIO.input(button)
	ledRedSts = GPIO.input(ledRed)
	ledYlwSts = GPIO.input(ledYlw)
	ledGrnSts = GPIO.input(ledGrn)
	
	motorASts = GPIO.input(button)
	motorBSts = GPIO.input(button)
	
	tempSts=str(last_soil_moisture_value)
	humiSts=str(last_humidity_value)
	waterSts=str(last_water_value)
	flameSts=str(last_flame_value)
	soilSts=str(last_soil_value)
	medicineMagnetSts=str(last_medicineMagent_value)

	
	templateData = {
      		'button'  : buttonSts,
      		'ledRed'  : ledRedSts,
      		'ledYlw'  : ledYlwSts,
      		'ledGrn'  : ledGrnSts,
      		'motorA'  : motorASts,
		'motorB'  : motorBSts,
		'temp'    : tempSts,
		'humidity' : humiSts,
		'water'    : waterSts,
		'flame'    : flameSts,
		'soil'    : soilSts,
		'medicine'    : medicineMagnetSts,

      	}
	return render_template('index.html', **templateData)
	
@app.route('/', methods=['POST'])
def get_values_from_serial():

      global last_soil_moisture_value
      global last_humidity_value
      global last_water_value
      global last_flame_value
      global last_soil_value
      global last_medicineMagent_value


      ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
      print("arduino connected!")
      while True:
        try:
            read_serial = ser.readline()
            #print(read_serial)
            #print("read Serial")
            #print(json.loads(read_serial.decode('utf-8')))
            read_json = json.loads(read_serial.decode('utf-8'))
            print(read_json)
            print(read_json['temperature'])
            if read_json['temperature'] is not None:
                print("not None 1")
                last_soil_moisture_value = float(read_json['temperature'])
                print(last_soil_moisture_value)
                if last_soil_moisture_value > 20.00:
                  print("bigger")
		  
            #print(last_soil_moisture_value)
            if read_json['humidity'] is not None:
                print("not None 2")
                last_humidity_value = float(read_json['humidity'])
                print(last_humidity_value)
		
            if read_json['water'] is not None:
                print("not None 3")
                last_water_value = float(read_json['water'])
                print(last_water_value)
                if last_water_value > 350.00:
                  print("flood")
                  msg = "watering!! (" + str(last_water_value) + "%)! had detected!"
                  send_mail(msg)
                  #break
		  
            if read_json['flame'] is not None:
                print("not None 4")
                last_flame_value = float(read_json['flame'])
                print(last_flame_value)
                if last_flame_value < 10.00:
                  print("flame")		  
		  
            if read_json['soil'] is not None:
                print("not None 4")
                last_soil_value = float(read_json['soil'])
                print(last_soil_value)
                if last_soil_value < 42.00:
                  print("soil")	
		  
            if read_json['medicineMagnet'] is not None:
                print("not None 5")
                last_medicineMagent_value = float(read_json['medicineMagnet'])
                print(last_medicineMagent_value)
                if last_medicineMagent_value == 0: #if medicine has close
                  print("medicineMagnet close")			  
                elif last_medicineMagent_value == 1: #if medicine has open
                  print("medicineMagnet open")			  
		  
		  
		  	  				
        except json.decoder.JSONDecodeError:
            pass
        except serial.serialutil.SerialException:
            pass



#send mail function
def send_mail(message):
    global mutex

    mutex.acquire()

    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()

    server.login(email,email_password)

    email_content = MIMEText(message, 'localhost')
    email_content['Subject'] = 'watering'

    server.sendmail(email, "tali.yanous@gmail.com", email_content.as_string())
    server.quit()

    print("Sent mail!")

    mutex.release()



# for example - /ledYlw/off --> deviceName=ledTlw, action=off	
@app.route("/<deviceName>/<action>")
def action(deviceName, action):
	if deviceName == 'ledRed':
		actuator = ledRed
	if deviceName == 'ledYlw':
		actuator = ledYlw
	if deviceName == 'ledGrn':
		actuator = ledGrn

	if deviceName == 'motorA':
		actuator = motorA

	if deviceName == 'motorB':
		actuator = motorB		
   
	if action == "on":
		GPIO.output(actuator, GPIO.HIGH)
	if action == "off":
		GPIO.output(actuator, GPIO.LOW)
		     
	buttonSts = GPIO.input(button)
	ledRedSts = GPIO.input(ledRed)
	ledYlwSts = GPIO.input(ledYlw)
	ledGrnSts = GPIO.input(ledGrn)
	
	motorASts = GPIO.input(motorA)
	motorBSts = GPIO.input(motorB)
	
	tempSts=str(last_soil_moisture_value)
	humiSts=str(last_humidity_value)
	waterSts=str(last_water_value)
	flameSts=str(last_flame_value)
	soilSts=str(last_soil_value)
	medicineMagnetSts=str(last_medicineMagent_value)


   
	templateData = {
	 	'button'  : buttonSts,
      		'ledRed'  : ledRedSts,
      		'ledYlw'  : ledYlwSts,
      		'ledGrn'  : ledGrnSts,
		'motorA'  : motorASts,
		'motorB'  : motorBSts,
		'temp'    : tempSts,
		'humidity' : humiSts,
		'water'    : waterSts,
		'flame'    : flameSts,
		'soil'    : soilSts,
		'medicine'    : medicineMagnetSts,


	}
	return render_template('index.html', **templateData)
      
temperature_thread = threading.Thread(target=get_values_from_serial)      

if __name__ == "__main__":
   temperature_thread.start()
   app.run(host='0.0.0.0', port=80, debug=True)
