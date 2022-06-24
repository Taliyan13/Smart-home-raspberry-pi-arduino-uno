'''
	Raspberry Pi GPIO Smart Home
'''
import RPi.GPIO as GPIO
from flask import Flask, render_template, request
import serial
import json
import threading
import time
from time import sleep
import os 
from flask import send_from_directory   
import smtplib
from email.message import EmailMessage

#pyrebase
import board
import busio as io
import adafruit_mlx90614
import pyrebase
import uuid
from gpiozero import Buzzer 
from datetime import datetime
import struct


#from apscheduler.schedulers.background import BackgroundScheduler
#from flask_apscheduler import APScheduler



app = Flask(__name__)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


#pyrebase details
config = {
  "apiKey": "AIzaSyCevUyd41KclpEFRa4FuqdRj98U_8FSTBM",
  "authDomain": "smart-home-ruppin-default-rtdb.firebaseio.com",
  "projectId": "smart-home-ruppin",
  "databaseURL": "https://smart-home-ruppin-default-rtdb.firebaseio.com",
  "storageBucket": "smart-home-ruppin.appspot.com",
  "messagingSenderId": "953452398862"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()
storage = firebase.storage() 


########################
   #global variabls#
########################
#user+password mail for mail function
sendTo = "tali.yanous@gmail.com"
clientMail = "ruppin.smarthome@gmail.com"


#########################
   #define GPIO sensors 
#########################

#define Air confition and Temperature GPIOs
fan = 22

#define buzzer (for panic button) GPIOs
#buzzer = 3

#define panic btn GPIOs
panicBtn = 10

#define door lock GPIOs
doorlockBtn = 23
magnetDoorlockBtn = 16
buzzerDoorlock=17
matchFlag = 0

#################################
#initialize GPIO status variables
#################################

#initialize Air confition and Temperature GPIOs
tempSts=0
fanSts=0
last_temperature_value = 0
last_humidity_value = 0
temp_value=0
ventilationSts= ''
html_fan_status =''

html_panicBtn_status = ''

# i'm ok system
okFridge=0
okMedicine=0

medicine3 = 0 # save state timer == 3 
fridge3 = 0 # save state timer == 3 


#initialize shutter GPIOs
servo1gpio = 27
servo2gpio = 18
html_shutter_status =''
shutterSts= ''
shutter_Sts=''
shutter_light_value=0


#initialize magnets GPIOs
last_medicineMagent_value = 0 #magnet for medicine check
medicineMagnetSts = 0
last_fridgeMagent_value = 0 #magnet for fridge check
fridgeMagnetSts = 0
saveStateFridge = 0 # for save data in DB
saveStateMedicine = 0
#initialize water GPIOs
last_water_value = 0
waterSts=0

#initialize flame GPIOs
last_flame_value = 0
flameSts=0

#initialize flame GPIOs
last_soil_value = 0
soilSts=0

#initialize watering system GPIOs
wateringSystemPin = 11
last_wateringSystem_value = 0
wateringSystemSts=0
html_wateringSystem_status =''

#initialize security system
html_securitySystem_status ='' # home door close/open

#initialize Heartbeat GPIOs
heartbeat_value=0
heartbeat_mail_alert=0

#initialize lights GPIOs
#bedroom
bedroom_light_pin=4
bedroom_light_Sts=0
#livingroom
livingroom_light_pin=5
livingoom_light_Sts=0
livingroomLight=5
#kitchen
#kitchen_light_pin=6
#kitchen_light_Sts=0
#garden
garden_light_pin=26
garden_light_Sts=0
#bathroom
bathroom_light_pin=25
bathroom_light_Sts=0
#emergency lighting
emergency_light_pin=24
emergency_light_value=0
	

# Set pins 11 as outputs, and define as PWM wateringServo
GPIO.setup(11,GPIO.OUT)
wateringServo = GPIO.PWM(11,50) # pin 11 for servo1
GPIO.setup(wateringSystemPin, GPIO.OUT)
GPIO.output(wateringSystemPin, GPIO.LOW)
# Start PWM running on both servos, value of 0 (pulse off)
wateringServo.start(0)
wateringDuty = 2



##############################################
# Define and setup pins as output/input
##############################################

#setup doorlock
GPIO.setup(doorlockBtn, GPIO.OUT)
GPIO.output(doorlockBtn, GPIO.LOW)

#setup new motor shutter
GPIO.setup(18, GPIO.OUT)
GPIO.setup(27, GPIO.OUT)
GPIO.setup(6, GPIO.OUT)
GPIO.output(18,GPIO.LOW)
GPIO.output(27,GPIO.LOW)
p=GPIO.PWM(6,1000)
p.start(75)

GPIO.setup(magnetDoorlockBtn, GPIO.IN)

#buzzer = Buzzer(17)
GPIO.setup(buzzerDoorlock, GPIO.OUT)
GPIO.output(buzzerDoorlock, GPIO.LOW)


# Set pins 11 & 12 as outputs, and define as PWM servo1 & servo2
#GPIO.setup(27,GPIO.OUT)
#servo1 = GPIO.PWM(27,50) # pin 11 for servo1
#GPIO.setup(18,GPIO.OUT)
#servo2 = GPIO.PWM(18,50) # pin 12 for servo2

#GPIO.setup(servo1gpio, GPIO.OUT)
#GPIO.setup(servo2gpio, GPIO.OUT)
#GPIO.output(servo1gpio, GPIO.LOW)
#GPIO.output(servo2gpio, GPIO.LOW)

# Define light pins as output
GPIO.setup(bedroom_light_pin, GPIO.OUT)   
GPIO.setup(livingroom_light_pin, GPIO.OUT) 
#GPIO.setup(kitchen_light_pin, GPIO.OUT)
GPIO.setup(garden_light_pin, GPIO.OUT) 
GPIO.setup(bathroom_light_pin, GPIO.OUT)  
GPIO.setup(emergency_light_pin, GPIO.OUT)  


# Define and setup pins as output/input for ventilation sensor
GPIO.setup(fan, GPIO.OUT)
GPIO.output(fan, GPIO.LOW)


# Define and setup pins as output/input for panic button sensor
GPIO.setup(panicBtn, GPIO.OUT)
GPIO.output(panicBtn, GPIO.LOW)


#initialize panic button GPIOs - user click in application
PanicBtnSts=0

#initialize panic button GPIOs - user hand click on button
last_panic_value = 0
PanicSts=0


###########FingerPrint#############
#for addfingerprintcheck
last_add_value = 0
idCounterDB = 1
userAddId = 0 #user id client want to add to DB - from html textbox
userAddName = '' #user name client want to add to DB - from html textbox

#for deletefingerprint
deleteId=0
userDeleteId = '' #user id client want to delete to DB - from html textbox
deletedfingerId = ''#catch the fingerid
usernameDeleted  = '' #catch the username 

#for open door lock
match_value = 0
###########FingerPrint#############


############
#strat
############
# Start PWM running on both servos, value of 0 (pulse off) - aircondition system
#servo1.start(0)
#servo2.start(0)
duty=90

#lighting system - turn leds OFF 
GPIO.output(bedroom_light_pin, GPIO.LOW)
GPIO.output(livingroom_light_pin, GPIO.LOW)
#GPIO.output(kitchen_light_pin, GPIO.LOW)
GPIO.output(garden_light_pin, GPIO.LOW)
GPIO.output(bathroom_light_pin, GPIO.LOW)
GPIO.output(emergency_light_pin, GPIO.LOW)


@app.route('/favicon.ico') 
def favicon(): 
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


#@app.route("/")
@app.route("/", methods=['GET','POST'])
def index():
	global html_shutter_status
	global last_medicineMagent_value
	global last_fridgeMagent_value
	global okFridge
	global okMedicine	
	global medicine3
	global fridge3
	
	# Read GPIO Status
	ventilationSts=change_html_status_string(GPIO.input(fan))
	#wateringSystemSts=change_html_status_string(GPIO.input(wateringServo))
	shutterSts=html_shutter_status 
	if request.method == 'POST' :
		if medicine3 == 3:
			okMedicine=1
		if fridge3 == 3:
			okFridge=1
		
	if (shutterSts == ''):
		shutterSts='off'
	  
	tempSts=str(last_temperature_value)
	humiditySts=str(last_humidity_value)
	medicineMagnetSts=str(last_medicineMagent_value)
	fridgeMagnetSts=str(last_fridgeMagent_value)
	waterSts=str(last_water_value)
	flameSts=str(last_flame_value)
	PanicSts=str(last_panic_value)
	soilSts=str(last_soil_value)

	
	templateData = {
		'temp'        : tempSts,
		'humidity'    : humiditySts,
		'ventilation' :ventilationSts,
		'medicine': medicineMagnetSts,
		'fridge' : fridgeMagnetSts,
		'water' : waterSts,
		'flame' : flameSts,
		'panic' : PanicSts,
		'watering' : wateringSystemSts, #was wateringSystem-need to check it
		'soil' : soilSts,
		'doorLock' : html_securitySystem_status,
		'shutter'     :shutterSts,


		
    }
    
	return render_template('index.html', **templateData )



@app.route("/health/", methods=['GET','POST'])	
def health_function():
	
	return render_template('health.html',panic = last_panic_value ,medicine = last_medicineMagent_value , fridge = last_fridgeMagent_value)			



@app.route("/heartbeat/", methods=['GET','POST'])	
def heartbeat_function():
	
	#return render_template('heartbeat.html',ht_value = heartbeat_mail_alert)
	return render_template('heartbeat.html',ht_value = heartbeat_value)	




@app.route("/safety/", methods=['GET','POST'])	
def safety_function():
	
	return render_template('safety.html', water = last_water_value , flame = last_flame_value )


@app.route("/wateringSystem/", methods=['GET','POST'])
def wateringSystem_function():
	return render_template('wateringSystem.html', watering=html_wateringSystem_status , soil=last_soil_value)
	
	
@app.route("/securitySystem/", methods=['GET','POST'])
def securitySystem_function():	
	return render_template('securitySystem.html', doorLock=html_securitySystem_status )


		

@app.route('/', methods=['POST'])
def get_values_from_serial():
	#global variables 
	global last_temperature_value
	global last_humidity_value
	global temp_value
	global last_medicineMagent_value
	global last_flame_value
	global last_water_value	
	global last_panic_value
	global last_fridgeMagent_value
	global last_soil_value
	global last_add_value
	global userAddId
	global match_value	
	global shutter_light_value
	global shutter_Sts
	global html_shutter_status
	global emergency_light_value
	global heartbeat_value
	global heartbeat_mail_alert
	global saveStateFridge
	global saveStateMedicine
	global matchFlag
	global okFridge
	global okMedicine
	global medicine3
	global fridge3
	global garden_light_Sts



      
	while True:
		try:
			read_serial = ser.readline()
			read_json = json.loads(read_serial.decode('utf-8'))
						
			print(read_json)


			#temperature
			if read_json['1'] is not None:
				last_temperature_value = float(read_json['1'])
				#print(last_temperature_value)
				
			#humidity    
			if read_json['2'] is not None:
				last_humidity_value = float(read_json['2'])
				#print(last_humidity_value)
					
			#medicine magnet    
			if read_json['3'] is not None:
				last_medicineMagent_value = float(read_json['3'])
				if last_medicineMagent_value == 1:
					if saveStateMedicine == 1:
						print("sent")
						
					else:	
						openMedicine()
					#counter for 1 time
				if last_medicineMagent_value == 0:
					saveStateMedicine = 0	
					
					
				#notification system - 					
				#that mean the human dosent open the medicine box for 3 hours. need to check everything ok.
				if last_medicineMagent_value == 3:
					medicine3 = 3
					msg = " Hi X, you should take medicine, 3 hours have passed."
					#email_alert("magnet", msg, clientMail)
				#that mean the human dosent open the fridge for 3 hours. send email to save account.
				if last_medicineMagent_value == 5:
					if okMedicine==1:
						print("all good")
						medicine3=0
						okMedicine=0
					else:
						msg = "X dont open medicine box for+ 5 hours"
						#email_alert("magnet", msg, sendTo)
						medicine3=0
						okMedicine=0
						print(msg)

			
			
			
			#fridge magnet    
			if read_json['7'] is not None:
				last_fridgeMagent_value = float(read_json['7'])
				#last time X open fridge
				if last_fridgeMagent_value == 1:
					if saveStateFridge == 1:
						print("sent")
						
					else:	
						openFridgeTime()
					#counter for 1 time
				if last_fridgeMagent_value == 0:
					saveStateFridge = 0	
					
				#notification system - 					
			 	#that mean the human dosent open the fridge for 3 hours. need to check everything ok.
				if last_fridgeMagent_value == 3:
					fridge3 = 3
					msg = "Hi X, a long time you didnt eat."
					#email_alert("fridge magnet", msg, clientMail)
				#that mean the human dosent open the fridge for 3 hours. send email to save account.
				if last_fridgeMagent_value == 5:
					if okFridge==1:
						print("all good")
						fridge3=0
						okFridge=0	
					else:
						msg = "X dont open the fridge for+ 5 hours"
						#email_alert("fridge magnet", msg, sendTo)
						fridge3 = 0	
						okFridge=0
						print(msg)					

				
				
			#water 
			if read_json['4'] is not None:
				last_water_value = float(read_json['4'])
				if last_water_value > 400:
					msg = "danderous! pls talk with X"
					#email_alert("house is flooded!", msg, clientMail)
					#email_alert("house is flooded!", msg, sendTo)
					#print(last_water_value)


			#flame		
			if read_json['5'] is not None:
				last_flame_value = float(read_json['5'])
				if last_flame_value < 20:
					msg = "danderous! pls talk with X"
					#email_alert("fire broke out!", msg, clientMail)
					#email_alert("fire broke out!", msg, sendTo)
				#print(last_flame_value)
								

			#panicBtn		
			if read_json['6'] is not None:
				#print("panicBtn")
				last_panic_value = float(read_json['6'])
				if last_panic_value == 1:
					msg1 = "X push the panic button"
					#email_alert("panic button", msg1, sendTo)
				#print(last_panic_value)
					
								
			#soil sensor for watering system		
			if read_json['8'] is not None:
				last_soil_value = float(read_json['8'])
				if last_soil_value < 800:
					#print("play watering system")
					#msg4 = "need to play watering system"
					#email_alert("watering system", msg4, sendTo)
					print(last_soil_value)
				
				
			#fingerPrint	
			# add new fingerprint to DB		
			if read_json['9'] is not None and read_json['10'] is not None:
				last_add_value = float(read_json['9'])
				matchFinger = float(read_json['10'])
				if  0 < last_add_value < 128 and matchFinger >0 :
					if matchFinger == 1:
						print("open door lock")
						openDoor()
						visitorOpenDoor(last_add_value)
					elif matchFinger == 2:
						print("dont find a finger match")
				if  0 < last_add_value < 128 and matchFinger == 0 :	
					addFingerprint()
					#firebase function
					#addFingerprint()
					
					
			# search for fingerprintid	
			#if read_json['10'] is not None:
			#	match_value = float(read_json['10'])	
			#	if match_value == 1:		
			#		print("open door lock")
			#		openDoor()
			#		visitorOpenDoor(last_add_value)
			#	if match_value == 2:
			#		print("dont find a finger match")


			# heartbeat	
			if read_json['11'] is not None:
				heartbeat_value=float(read_json['11'])
				if 60 < heartbeat_value < 100 :
					msg = "heatBeat test"
					email_alert("dayli hertbeat test- " + str(heartbeat_value), msg, clientMail)
					email_alert("heartbeat system", msg, sendTo)
					heartBeatCheck(heartbeat_value)					
					
				if (heartbeat_value>0 and heartbeat_value<60) or (heartbeat_value>100):
					msg = "call to doctor"
					email_alert("heartbeat system", msg, clientMail)
					email_alert("heartbeat system", msg, sendTo)
					heartBeatCheck(heartbeat_value)
				#print(heartbeat_value)					
					
					
			if read_json['12'] is not None:
				print("not none enregency")
				emergency_light_value=float(read_json['12'])
				print(emergency_light_value)
				if (emergency_light_value < 370.0 and GPIO.input(livingroom_light_pin) == 0):
					change_action_status(emergency_light_pin, "on")
				if (emergency_light_value > 500.0 or GPIO.input(livingroom_light_pin) == 1):
					change_action_status(emergency_light_pin, "off")					


			if read_json['13'] is not None:
				
				print(html_shutter_status)
				shutter_light_value=float(read_json['13'])
				print(shutter_light_value)
				if (shutter_light_value < 500.0 and html_shutter_status == 'on'):
					shutter_Sts=change_2_actions_status(servo1gpio,servo2gpio, "off")
					change_action_status(garden_light_pin, "on")
					garden_light_Sts = GPIO.input(garden_light_pin)
					html_shutter_status=change_html_status_string(shutter_Sts)
					
					
					print("go into shutter_light_value - on")
				if (shutter_light_value > 600.0 and html_shutter_status == 'off'):
					shutter_Sts=change_2_actions_status(servo1gpio,servo2gpio, "on")
					html_shutter_status=change_html_status_string(shutter_Sts)
					change_action_status(garden_light_pin, "off")
					garden_light_Sts = GPIO.input(garden_light_pin)	
					print("go into shutter_light_value - off")
					
		

				
		except json.decoder.JSONDecodeError:
		    pass
		except serial.serialutil.SerialException:
		    pass
 
@app.route("/aircondition/", methods=["GET","POST"])
def air_condition_function():
                if request.method == 'POST' :
                  temp_value=request.form.get("tvalue")
                  fanSts = GPIO.input(fan)
                  print(temp_value)
                  print(fanSts)
                  print(last_temperature_value)
                  if (last_temperature_value > float(temp_value) and GPIO.input(fan) == 0):
                     print("bigger")
                     GPIO.output(fan, GPIO.HIGH)
                  if (last_temperature_value < float(temp_value) and GPIO.input(fan) == 1):
                     print("littel then")
                     GPIO.output(fan, GPIO.LOW) 
                fanSts = GPIO.input(fan)
                html_fan_status=change_html_status_string(GPIO.input(fan))
                print(fanSts)       
                return render_template('aircondition.html',value=fanSts,ventilation=html_fan_status )
                 

		
@app.route("/shutter/", methods=["GET","POST"])
def shutter_function():
	global html_shutter_status
	global shutter_light_value
	if (html_shutter_status == ''):
		html_shutter_status='off'
	print("shutter function")
	return render_template('shutter.html',value=shutter_Sts, shutter=html_shutter_status,light_stutterpage_value= shutter_light_value)
	

	
@app.route("/lighting/", methods=["GET","POST"])
def lighting_function():
	# Read GPIO Status
			bedroom_light_Sts = GPIO.input(bedroom_light_pin)
			livingoom_light_Sts = GPIO.input(livingroom_light_pin)
			#kitchen_light_Sts = GPIO.input(kitchen_light_pin)
			garden_light_Sts = GPIO.input(garden_light_pin)
			bathroom_light_Sts = GPIO.input(bathroom_light_pin)
	
			lightTemplateData = {
				'bedroom_light'     : bedroom_light_Sts,
				'livingroom_light'  : livingoom_light_Sts,
				#'kitchen_light'     : kitchen_light_Sts,
				'bathroom_light'    : bathroom_light_Sts,
				'garden_light'      : garden_light_Sts
      			
				}
			return render_template('lighting.html', **lightTemplateData )

	         
@app.route("/systemControl/<deviceName>/<action>")
def action(deviceName, action):
		#global variables   
		global shutter_Sts
		global html_shutter_status
		global heartbeat_value  
		global heartbeat_mail_alert    
		
		if deviceName == 'ventilation':
			actuator = fan
			change_action_status(actuator, action)
			fanSts= GPIO.input(fan)
			html_fan_status=change_html_status_string(GPIO.input(fan))
			return render_template('aircondition.html', value=fanSts, ventilation=html_fan_status )
			
			
		
		if deviceName == 'shutter':
			actuator1 = servo1gpio
			actuator2 = servo2gpio
			shutter_Sts=change_2_actions_status(actuator1, actuator2, action)
			html_shutter_status=change_html_status_string(shutter_Sts)
			print("shetter")
			print(html_shutter_status)
			

			return render_template('shutter.html', value=shutter_Sts, shutter=html_shutter_status )
			
		if (deviceName == 'livingroomLight' or  deviceName == 'kitchenLight' or deviceName == 'bedroomLight' or deviceName == 'bathroomLight' or deviceName == 'gardenLight'):
			if deviceName == 'livingroomLight': actuator=livingroom_light_pin
			if deviceName == 'bedroomLight' : actuator=bedroom_light_pin
			#if deviceName == 'kitchenLight': actuator=kitchen_light_pin
			if deviceName == 'gardenLight': actuator=garden_light_pin
			if deviceName == 'bathroomLight': actuator=bathroom_light_pin
			change_action_status(actuator, action)
			
			bedroom_light_Sts = GPIO.input(bedroom_light_pin)
			livingoom_light_Sts = GPIO.input(livingroom_light_pin)
			#kitchen_light_Sts = GPIO.input(kitchen_light_pin)
			garden_light_Sts = GPIO.input(garden_light_pin)
			bathroom_light_Sts = GPIO.input(bathroom_light_pin)
	
			lightTemplateData = {
				'bedroom_light'    : bedroom_light_Sts,
				'livingroom_light' : livingoom_light_Sts,
				#'kitchen_light'    : kitchen_light_Sts,
				'bathroom_light'   : bathroom_light_Sts,
				'garden_light'     : garden_light_Sts
      			
				}
			return render_template('lighting.html', **lightTemplateData )
						
						
		if deviceName == 'panicButton':
			#need to send SMS and play buzzer
			actuator = panicBtn
			change_action_status(actuator, action)
			last_panic_value= GPIO.input(panicBtn)
			#html_panicBtn_status=change_html_status_string(GPIO.input(panicBtn))
			if last_panic_value == 1 :
				msg2 = "X push the panic button"
				email_alert("panic button", msg2, sendTo)
				return render_template('health.html' , panic = last_panic_value ,medicine = last_medicineMagent_value , fridge = last_fridgeMagent_value)			
			return render_template('health.html',panic = last_panic_value ,medicine = last_medicineMagent_value , fridge = last_fridgeMagent_value)			

			
		if deviceName == 'panicButtonMainPage':
			#need to send SMS and play buzzer
			actuator = panicBtn
			change_action_status(actuator, action)
			last_panic_value= GPIO.input(panicBtn)
			#html_panicBtn_status=change_html_status_string(GPIO.input(panicBtn))
			if last_panic_value == 1 :
				msg2 = "X push the panic button"
				email_alert("panic button", msg2, sendTo)
				return render_template('index.html' , panic = last_panic_value ,medicine = last_medicineMagent_value , fridge = last_fridgeMagent_value)
			return render_template('index.html', panic = last_panic_value ,medicine = last_medicineMagent_value , fridge = last_fridgeMagent_value)
			
			
		if deviceName == 'heartbeat':			
			print("heartbeat action function")
			ser.write(b'heartbeat\n')
			#return render_template('heartbeat.html',ht_value = heartbeat_mail_alert)
			return render_template('heartbeat.html',ht_value = heartbeat_value)			

 
 
  
#change action on->off or off->on  
def change_action_status(actuator, action):
		if action == "on":
			GPIO.output(actuator, GPIO.HIGH)
				
		if action == "off":
			GPIO.output(actuator, GPIO.LOW)
			

			
#change action on->off or off->on  
#def change_2_actions_status(actuator1,actuator2, action):
#		#global variables   
#		global duty
#		if action == "on":
#			if duty == 13 or html_shutter_status == 'on' :
#				print("alredy open")
#				#continue
#			else:
#				print("else")
#				# Define variable 
#				duty = 2
#				# Loop for duty values from 2 to 12 (0 to 180 degrees)
#				while duty <= 12:
#					print(duty)
#					servo1.ChangeDutyCycle(duty)
#					servo2.ChangeDutyCycle(duty)
#					time.sleep(0.5)
#					duty = duty + 1
#					print(duty)
#				# Wait a couple of seconds
#				time.sleep(2)
#				GPIO.output(27,GPIO.LOW)
#				GPIO.output(18,GPIO.LOW)
#				#Clean things up at the end
#				servo1.start(0)
#				servo2.start(0)
#				#GPIO.cleanup()
#				print ("Goodbye") 
#				return 1;
#		if action == "off":
#			if duty ==1 or  html_shutter_status == 'off':
#				print("alredy close")
#				#continue
#			else:
#				print("off")
#				# Define variable duty
#				duty = 12
#				# Loop for duty values from 12 to 2 (180 to 0 degrees)
#				while duty >= 2:
#					servo1.ChangeDutyCycle(duty)
#					servo2.ChangeDutyCycle(duty)
#					time.sleep(0.5)
#					duty = duty - 1
#				# Wait a couple of seconds
#				time.sleep(2)
#				GPIO.output(27,GPIO.LOW)
#				GPIO.output(18,GPIO.LOW)
#				#Clean things up at the end
#				servo1.start(0)
#				servo2.start(0)
#				#GPIO.cleanup()
#				print ("Goodbye")
#				return 0;
						
def change_2_actions_status(actuator1,actuator2, action):
	print("in shutter function")
	if action == "on":
		GPIO.output(18,GPIO.HIGH)
		GPIO.output(27,GPIO.LOW)
		time.sleep(10)
		GPIO.output(18,GPIO.LOW)
		return 1
	
	if action == "off":
		GPIO.output(18,GPIO.LOW)
		GPIO.output(27,GPIO.HIGH)
		time.sleep(10)
		GPIO.output(27,GPIO.LOW)
		return 0
		
		
#change action on->off or off->on  
@app.route("/add_or_delete_fingerprint/<action>", methods=["GET","POST"])
def add_or_delete_fingerprint(action):
		global userAddId
		global userAddName
		global deletedfingerId #catch the fingerid
		global usernameDeleted #catch the username 
		
		if action == "add":
			if request.method == 'POST' :
				userAddId=request.form.get("userAddID")
				userAddName=request.form.get("userAddName")
				print(userAddId)
				if idCounterDB < 128:
					ser.write(b'addFingerPrint\n')
					
				else:
					print("there is no space in DB")
				
		if action == "delete":
			if request.method == 'POST' :	
				print("post delet")			
				# 1. go to DB and find user id
				# if exists - deletedfunc() + write.ser to arduino
				# if not exists - msg
				
				
				testid=request.form.get("userDeleteID")
				print(testid)
				if(deleteFingerprint(testid) == True):
					print("true if")
					fingerid = int(deletedfingerId)
					print("after int casting")
					print(fingerid)
					
					var= '%deleteFingerPrint:'+ str(fingerid)+ '%' + '\n'
					varnew=bytes(var, 'utf8')
					print(varnew)
					#if we found user with relevant id - send to arduino the fingerprintid
					ser.write(varnew)
				else:
					print("user not exists")
				
					
		if action == "open":
			if request.method == 'POST' :
				ser.write(b'openDoorLock\n')

					
										
			
		return render_template('securitySystem.html', doorLock=html_securitySystem_status )
	


			
				
#change action int->string: 1=>on , 0=>off
def change_html_status_string(status):
		if status == 1:
			return "on"
		elif status == 0:
			return "off"

          
def email_alert(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)
    msg['subject'] = subject
    msg['to'] = to

    user = "ruppin.smarthome@gmail.com"
    msg['from'] = user
    password = "fyevqigxnijvhodg"
    
    server = smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()

    server.login(user, password)

    server.send_message(msg)
    server.quit()

	
#add new fingerprint to DB
def addFingerprint():
  global idCounterDB
  global userAddId
  global userAddName
  
  dbid = last_add_value

  dbidfingerprint= float(dbid)
  usridfingerprint = float(userAddId)
  usrnamefingerprint = str(userAddName)
  uu = str(uuid.uuid1())
  data = {
    "fingerid": dbidfingerprint,
    "userid": usridfingerprint,
    "username": usrnamefingerprint,

  }
  
  db.child("fingerprint").child(uu).set(data)
  

  idCounterDB = idCounterDB + 1
  time.sleep(2)
  
  
  	
#delete exiting fingerprint from DB
def deleteFingerprint(userDeleteId):
  global deleteId #here we will save the last id number was deleted, for new id number
  global idCounterDB
  global deletedfingerId #catch the fingerid
  global usernameDeleted #catch the username  
  
  fingers = db.child("fingerprint").get()
  for index,finger in enumerate(fingers.each()):
	  if finger.val() != None:
		  print(finger.val())
		  print(finger.val()['userid'])
		  print("usrID")
		  print(userDeleteId)
		  if str(finger.val()['userid']) == str(userDeleteId):
			  key=finger.key()
			  print("pybase finger id")
			  print(finger.val()['fingerid'])
			  #save the fingerid for specific userId we want to delete, for send to arduino deletefingerpront func
			  deletedfingerId = finger.val()['fingerid'] 
			  #save user name for msg in html
			  usernameDeleted = finger.val()['username']
			  
			  print("remove")
			  db.child("fingerprint").child(key).remove()
			  return True
		  else:
			  print("userid not exists")  
			  return False

	
  
  time.sleep(2)
    

def openDoor():
	global match_value
	global matchFlag
	
	matchFlag=0
	print("doorlock")
	print(GPIO.input(doorlockBtn))
	print("magnet")
	print(GPIO.input(magnetDoorlockBtn))
	GPIO.output(doorlockBtn, GPIO.HIGH)
	time.sleep(7)
	print(GPIO.input(magnetDoorlockBtn))
	if GPIO.input(magnetDoorlockBtn) == 1:
		loop_start_time = time.time()
		while(GPIO.input(magnetDoorlockBtn)==1):
			print("jjjj")
			if time.time()> 2 :
				print("buzzer")
				GPIO.output(buzzerDoorlock, GPIO.HIGH)
				#bezzer.on()
				time.sleep(0.5)
				GPIO.output(buzzerDoorlock, GPIO.LOW)
				#bezzer.off()			
				time.sleep(0.5)
				
	if GPIO.input(magnetDoorlockBtn) ==0 :
		print("if no")
		GPIO.output(doorlockBtn, GPIO.LOW)


def openFridgeTime():
  global saveStateFridge
  global last_fridgeMagent_value
  
  now = datetime.now() # current date and time
  date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
  #print("date_time")
  #print(date_time)
  
  uu = str(uuid.uuid1())
  data = {
    "last_time": date_time,

  }

  db.child("openFridge").child(uu).set(data)
  saveStateFridge=last_fridgeMagent_value
  time.sleep(2)


def openMedicine():
  global saveStateMedicine
  global last_medicineMagent_value
  
  now = datetime.now() # current date and time
  date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
  print("date_time")
  print(date_time)
  
  uu = str(uuid.uuid1())
  data = {
    "last_time": date_time,
  }

  db.child("medicine").child(uu).set(data)
  saveStateMedicine=last_medicineMagent_value
  time.sleep(2)    





def visitorOpenDoor(last_add_value):
	#global last_add_value #finger id
	
  fingers = db.child("fingerprint").get()
  for index,finger in enumerate(fingers.each()):
	  if finger.val() != None:
		  if str(finger.val()['fingerid']) == str(last_add_value):
			  key=finger.key()
			  visitUserID = finger.val()['userid'] 
			  now = datetime.now() # current date and time
			  date_time = now.strftime("%d/%m/%Y, %H:%M:%S")			  
			  visitUserName = finger.val()['username']
			  uu = str(uuid.uuid1())			  
			  data = {
			    "time": date_time,
			    "user_id": visitUserID,
			    "user_name": visitUserName,
			  }

			  db.child("visitor").child(uu).set(data)			  

			  
		  else:
			  print("userid not exists")  
			  
time.sleep(2)			  
			  
	
	

def heartBeatCheck(heartbeat_value):
	#global last_add_value #finger id
  now = datetime.now() # current date and time
  date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
  
  uu = str(uuid.uuid1())
  data = {
	"time": date_time,
    "heartBeat": heartbeat_value,	
  }
  
  db.child("heartBeatTests").child(uu).set(data)
			  
			 	
		  
			    
    	  
temperature_thread = threading.Thread(target=get_values_from_serial)
if __name__ == "__main__":
   ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
   print("arduino connected!")
   temperature_thread.start()
   app.run(host='0.0.0.0', port=80, debug=True)
