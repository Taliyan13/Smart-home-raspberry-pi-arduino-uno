'''
	Raspberry Pi GPIO Smart Home
'''
import RPi.GPIO as GPIO
from flask import Flask, render_template, request
import serial
import json
import threading
import time
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



app = Flask(__name__)
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


#pyrebase details
config = {
  "apiKey": "jRsmU1UrhE1sQlFlFmghTnF5fmiuFYkEaUjS8uxO",
  "authDomain": "smarthome-84e0e-default-rtdb.firebaseio.com",
  "databaseURL": "https://smarthome-84e0e-default-rtdb.firebaseio.com",
  "storageBucket": "smarthome-84e0e.appspot.com"
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

#initialize magnets GPIOs
last_medicineMagent_value = 0 #magnet for medicine check
medicineMagnetSts = 0
last_fridgeMagent_value = 0 #magnet for fridge check
fridgeMagnetSts = 0

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


# Set pins 11 as outputs, and define as PWM wateringServo
GPIO.setup(11,GPIO.OUT)
wateringServo = GPIO.PWM(11,50) # pin 11 for servo1
GPIO.setup(wateringSystemPin, GPIO.OUT)
GPIO.output(wateringSystemPin, GPIO.LOW)
# Start PWM running on both servos, value of 0 (pulse off)
wateringServo.start(0)
wateringDuty = 2




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


#for open door lock
match_value = 0
###########FingerPrint#############



@app.route('/favicon.ico') 
def favicon(): 
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route("/")
def index():
	# Read GPIO Status
	ventilationSts=change_html_status_string(GPIO.input(fan))
	#wateringSystemSts=change_html_status_string(GPIO.input(wateringServo))

	  
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

		
    }
	return render_template('index.html', **templateData )



@app.route("/health/", methods=['GET','POST'])	
def health_function():

	return render_template('health.html',panic = last_panic_value ,medicine = last_medicineMagent_value , fridge = last_fridgeMagent_value)



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

      
	while True:
		try:
			read_serial = ser.readline()
			read_json = json.loads(read_serial.decode('utf-8'))
						
			print(read_json)


			#temperature
			if read_json['1'] is not None:
				last_temperature_value = float(read_json['1'])
				print(last_temperature_value)
			#humidity    
			if read_json['2'] is not None:
				last_humidity_value = float(read_json['2'])
				print(last_humidity_value)
					
			#medicine magnet    
			if read_json['3'] is not None:
				last_medicineMagent_value = float(read_json['3'])
				#that mean the human dosent open the medicine box for 3 hours. need to check everything ok.
				if last_medicineMagent_value == 3:
					msg = " Hi X, you should take medicine, 3 hours have passed."
					#email_alert("magnet", msg, clientMail)
				#that mean the human dosent open the fridge for 3 hours. send email to save account.
				if last_medicineMagent_value == 5:
					msg = "X dont open medicine box for+ 5 hours"
                    #email_alert("medicine magnet", msg, sendTo)	
                    #print(last_medicineMagent_value)
			
			
			#fridge magnet    
			if read_json['7'] is not None:
				last_fridgeMagent_value = float(read_json['7'])
			 	#that mean the human dosent open the fridge for 3 hours. need to check everything ok.
				if last_fridgeMagent_value == 3:
					msg = "Hi X, a long time you didnt eat."
					#email_alert("fridge magnet", msg, clientMail)
				#that mean the human dosent open the fridge for 3 hours. send email to save account.
				if last_fridgeMagent_value == 5:
					msg = "X dont open the fridge for+ 5 hours"
					#email_alert("fridge magnet", msg, sendTo)	
					#print(last_fridgeMagent_value)
				
				
			#water 
			if read_json['4'] is not None:
				last_water_value = float(read_json['4'])
				#if last_water_value > X:
					#msg = "danderous! pls talk with X"
					#email_alert("house is flooded!", msg, sendTo)
					#print(last_water_value)


			#flame		
			if read_json['5'] is not None:
				last_flame_value = float(read_json['5'])
				#if last_flame_value > X:
					#msg = "danderous! pls talk with X"
					#email_alert("fire broke out!", msg, sendTo)
				#print(last_flame_value)
								

			#panicBtn		
			if read_json['6'] is not None:
				#print("panicBtn")
				last_panic_value = float(read_json['6'])
				if last_panic_value == 1:
					msg1 = "X push the panic button"
					email_alert("panic button", msg1, sendTo)
				#print(last_panic_value)
					
								
			#soil sensor for watering system		
			if read_json['8'] is not None:
				last_soil_value = float(read_json['8'])
				if last_soil_value > 800:
					print("play watering system")
					#play watering system
					#change_wateringSystem_status(wateringSystemPin,"on")
				#print(last_soil_value)
				
				
			#fingerPrint	
			# add new fingerprint to DB		
			if read_json['9'] is not None:
				last_add_value = float(read_json['9'])
				if  0 < last_add_value < 128:
					#firebase function
					addFingerprint()
					
			# search for fingerprintid	
			if read_json['10'] is not None:
				match_value = float(read_json['10'])
				if  match_value == 1:
					print("open door lock")
				if  match_value == 2:
					print("dont find a finger match")



				
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
                 
         
@app.route("/systemControl/<deviceName>/<action>")
def action(deviceName, action):      
		if deviceName == 'ventilation':
			actuator = fan
			change_action_status(actuator, action)
			fanSts= GPIO.input(fan)
			html_fan_status=change_html_status_string(GPIO.input(fan))
			return render_template('aircondition.html', value=fanSts, ventilation=html_fan_status )
			
		if deviceName == 'heartbeat':
			ser.write(deviceName.encode())
			ser.write(b'\n')
			return render_template('health.html')
			
			
		if deviceName == 'wateringSystem':
			actuator = wateringSystemPin
			change_wateringSystem_status(actuator, action)
			html_wateringSystem_status = change_html_status_string(GPIO.input(wateringSystemPin))
			print(html_wateringSystem_status)
			return render_template('wateringSystem.html', watering=html_wateringSystem_status )  
			
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
			return render_template('health.html', panic = last_panic_value ,medicine = last_medicineMagent_value , fridge = last_fridgeMagent_value)
			
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
			


 
 
  
#change action on->off or off->on  
def change_action_status(actuator, action):
		if action == "on":
			GPIO.output(actuator, GPIO.HIGH)
				
		if action == "off":
			GPIO.output(actuator, GPIO.LOW)
			
			

#change action on->off or off->on  
@app.route("/add_or_delete_fingerprint/<action>", methods=["GET","POST"])
def add_or_delete_fingerprint(action):
		global userAddId
		global userAddName
		
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
				userDeleteId=request.form.get("userDeleteID")
				print(userDeleteId)
				print(idCounterDB)
				if idCounterDB > 0:
					deleteFingerprint(userDeleteId)
					
		if action == "open":
			if request.method == 'POST' :
				ser.write(b'openDoorLock\n')

					
										
			
		return render_template('securitySystem.html', doorLock=html_securitySystem_status )
	


#change action on->off or off->on  
def change_wateringSystem_status(actuator, action):
	#global variables
	global wateringDuty
					
	if action == "on" :
		if wateringDuty == 13 :
				print("alredy open")
				#continue
		else:
			print("on")
			# Define variable 
			wateringDuty = 2
			# Loop for duty values from 2 to 12 (0 to 180 degrees)
			while wateringDuty <= 12 :
					wateringServo.ChangeDutyCycle(wateringDuty)
					time.sleep(0.5)
					wateringDuty = wateringDuty + 1
					# Wait a couple of seconds
					time.sleep(2)	
					GPIO.output(11,GPIO.LOW)
					#Clean things up at the end
					wateringServo.start(100)
					#GPIO.cleanup()
					print ("Goodbye")             
	if action == "off" :
		if wateringDuty ==1 :
				print("alredy close")
				#continue
		else:
			print("off")
			# Define variable duty
			wateringDuty = 12
			# Loop for duty values from 12 to 2 (180 to 0 degrees)
			while wateringDuty >= 2 :
				wateringServo.ChangeDutyCycle(wateringDuty)
				time.sleep(0.5)
				wateringDuty = wateringDuty - 1
				# Wait a couple of seconds
				time.sleep(2)
				GPIO.output(11,GPIO.LOW)
				#Clean things up at the end
				wateringServo.start(0)
				#GPIO.cleanup()
				print ("Goodbye")	
			
				
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
  #ref = db.reference('smarthome-84e0e-default-rtdb')

  
  fingers = db.child("fingerprint").get()
  for index,finger in enumerate(fingers.each()):
	  if finger.val() != None:
		  print(finger.val())
		  print(finger.val()['userid'])
		  print("usrID")
		  print(userDeleteId)
		  if str(finger.val()['userid']) == str(userDeleteId):
			  key=finger.key()
			  idCounterDB = idCounterDB - 1
			  print("remove")
			  
			  db.child("fingerprint").child(key).remove()
		  else:
			  print("userid not exists")  

	
  
  time.sleep(2)
    
    
    	  
temperature_thread = threading.Thread(target=get_values_from_serial)
if __name__ == "__main__":
   ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
   print("arduino connected!")
   temperature_thread.start()
   app.run(host='0.0.0.0', port=80, debug=True)
