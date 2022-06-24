//#include <HX711.h>
#include "DHT.h"
#include "string.h"
#include "stdio.h"
#include "stdlib.h"
#include <TaskScheduler.h>
#include <Adafruit_Fingerprint.h>
#include <SoftwareSerial.h>

//fingerprint sensor
SoftwareSerial mySerial(2, 3);
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);
uint8_t id = 1;

//define temp
#define DHTPIN 12     // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11   // DHT 11
//define heartbit 
#define samp_siz 4
#define rise_threshold 5
//define water sensor
#define POWER_PIN  7
#define WaterSIGNAL_PIN A2
//define fingerprint
#define MAX 127

//define magnet sensor

// We declare the function that we are going to use - function for task scheduler for magnets
void task_manager();

//for water sensor
int waterValue = 0; // variable to store the sensor value

//for flame sensor
int led = 13; // define the LED pin
int flameDigitalPin = 5; // KY-026 digital interface
int flameAnalogPin = A0; // KY-026 analog interface
int flameDigitalVal; // digital readings
int flameAnalogVal; //analog readings

//for buzzer - work with medicine and fridge magnet, flame and water sensors
const int buzzer = 0;   // (was pin 3 )need to change to another pin, flame with the same numPin

//for medicine magnet sensor
const int medicineMagnetsensorPin = 4;
int medicineMagnetSensorState; // 0 close - 1 open 
int saveMedicineState = 0; // save the current status for medicine box
int counterForMedicine = 0; //how many times there was no status change


//for fridge magnet sensor
const int fridgeMagnetsensorPin = 8;
int fridgeMagnetSensorState;
int saveFridgeState = 0; // save the current status for fridge
int counterForFridge = 0; //how many times there was no status change

//scheduler for medicine and fridge magnets 
// We create the Scheduler that will be in charge of managing the tasks
Scheduler runner;
// We create the task indicating that it runs every 5000 milliseconds, forever, and call the task_manager function
Task TareaLED(5000, TASK_FOREVER, &task_manager);


//for panicButton
// set pin numbers:
const int buttonPin = 6;     // the number of the pushbutton pin
//const int ledPin =  13;      // the number of the LED pin ----> we alredy have led pin 13 in code, we can use him.
// variables will change:
int buttonState = 0;         // variable for reading the pushbutton status

//for soil sensor
int soilSensorPin = A1; 
int soilSensorValue;  


//for temp sensor - run all the time
float h;
float t;


//for temp sensor- run when user click
float hum;
float tem;


//for heartbeat sensor
int heartBit_sensorPin = 3;
float print_value;
float sum_heartbeat = 0;
float avg_heartbeat = 0;
float hbbb=0;

//for fingerprint queue
int item = 0;
int rear = -1;
int front = -1;
int queue[MAX] = {0};
int i=0;

const int ledPin=11;
String nom = "Arduino";
String msg;
String msg1;
String deletedId;
uint8_t first;


//for globals 

String json ="";
char jsonData[256] = {'\0'}; /* Defined globally choose size large enough */

// need to remove, only for check we get user click on raspberry
int fungerprintToRasp = 0;
//match value for getfingerid() function
int matchFinger=0;






DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
  while (!mySerial);  // For Yun/Leo/Micro/Zero/...
  delay(100);
  // fingerprint sensor - set the data rate for the sensor serial port
  finger.begin(57600);
  if (finger.verifyPassword()) {
     //Serial.println("Found fingerprint sensor!");
   } else {
     //Serial.println("Did not find fingerprint sensor :(");
     while (1) { delay(1); }
   }
  finger.getParameters();

  //for water sensor
  pinMode(POWER_PIN, OUTPUT);   // configure D7 pin as an OUTPUT
  digitalWrite(POWER_PIN, LOW); // turn the water sensor OFF

  //for temp and humidity sensor
  dht.begin();

  //for flame sensor
  pinMode(led, OUTPUT);
  pinMode(flameDigitalPin, INPUT);  

  //for magnet sensor
  pinMode(medicineMagnetsensorPin, INPUT_PULLUP);

  //for fridge magnet
  pinMode(fridgeMagnetsensorPin, INPUT_PULLUP);

  
  // We add the task to the task scheduler
  runner.addTask(TareaLED);
  // We activate the task
  TareaLED.enable();

  //for panic button
  // initialize the pushbutton pin as an input:
  pinMode(buttonPin, INPUT);


  finger.getTemplateCount();

  if (finger.templateCount == 0) {
    //Serial.print("Sensor doesn't contain any fingerprint data. Please run the 'enroll' example.");
  }
  else {
    //Serial.println("Waiting for valid finger...");
      //Serial.print("Sensor contains "); Serial.print(finger.templateCount); Serial.println(" templates");
  }
}



void loop() {
  
  //heartbit 
   float reads[samp_siz], sum;
   long int now, ptr;
   float last, reader, start;
   float first, second, third, before;
   bool rising;
   int rise_count;
   int n;
   long int last_beat;
   float heartValue;
   int heartbeat_counter = 10;
   float raspberry_heartbeat=50.0;
   int ht_counter;
   
   //global
   

   //soil sensor
    soilSensorValue = analogRead(soilSensorPin); 


   //water sensor
   digitalWrite(POWER_PIN, HIGH);  // turn the water sensor ON
   delay(10);                      // wait 10 milliseconds
   waterValue = analogRead(WaterSIGNAL_PIN); // read the analog value from sensor
   digitalWrite(POWER_PIN, LOW);   // turn the sensor OFF

  //flame sensor
  // Read the digital interface
  flameDigitalVal = digitalRead(flameDigitalPin); 
  // Read the analog interface
  flameAnalogVal = analogRead(flameAnalogPin); 

  //medicine magnet sensor
  // 0 - close
  // 1 - open
  medicineMagnetSensorState = digitalRead(medicineMagnetsensorPin);


  //fridge magnet sensor
  fridgeMagnetSensorState = digitalRead(fridgeMagnetsensorPin);
  
  // It is necessary to run the runner on each loop
  runner.execute();


  //panic button
  // read the state of the pushbutton value:
  buttonState = digitalRead(buttonPin);

  //emergencyLight Sensor
  //reads the input on analog pin A4 (value between 0 and 1023) -- livingroom
  int emergencyLight = analogRead(A4);

  //sutterLight sensor - for shutter and garden
  int sutterLight = analogRead(A5);

              
   readSerialPort();
   //Serial.println(msg);
   //for delete fingerprint
   boolean isExists = msg.indexOf("%");
   //Serial.println(isExists);
   if(isExists != -1)
   {
    //Serial.println(msg);
    // Split the readString by a pre-defined delimiter in a simple way. '%'(percentage) is defined as the delimiter in this project.
    int delimiter, delimiter_1, delimiter_2, delimiter_3;
    delimiter = msg.indexOf("%");
    delimiter_1 = msg.indexOf(":", delimiter + 1);
    delimiter_2 = msg.indexOf("%", delimiter_1 +1);
    
    // Define variables to be executed on the code later by collecting information from the readString as substrings.
    msg1 = msg.substring(delimiter + 1, delimiter_1);
    deletedId = msg.substring(delimiter_1 + 1, delimiter_2);
    
    
    //Serial.println(msg);
    //Serial.println(deletedId);

  }

   
  //temp and humidity sensor
   hum = dht.readHumidity();
   // Read temperature as Celsius (the default)
   tem = dht.readTemperature();

  
    if (id == 0) {// ID #0 not allowed, try again!
       return;
    }
   
   //for save more space in json string, we need to convert large word to small one.
   //1 = temperature
   //2 = humidity
   //3 = medicineMagnet
   //4 = water
   //5 = flame
   //6 = panicBtn
   //7 = fridgeMagnet
   //8 = soil
   //9 = fingerprint
   //10 = matchFinger
   //11 = heartbeat
   //12 = emergencyLight
   //13 = sutterLight
   
   hbbb = analogRead(heartBit_sensorPin); 
   json = "{\"1\":\""+String(tem)+"\",\"2\":\""+String(hum)+"\",\"3\":\""+String(medicineMagnetSensorState)+"\",\"4\":\""+String(waterValue)+"\",\"5\":\""+String(flameAnalogVal)+"\",\"6\":\""+String(buttonState)+"\",\"7\":\""+String(fridgeMagnetSensorState)+"\",\"8\":\""+String(soilSensorValue)+"\",\"9\":\""+String(fungerprintToRasp)+"\",\"10\":\""+String(matchFinger)+"\",\"11\":\""+String(avg_heartbeat)+"\",\"12\":\""+String(emergencyLight)+"\",\"13\":\""+String(sutterLight)+"\"}";
   Serial.println(json);


   delay(1000);

   if(fungerprintToRasp > 0)
   {
    fungerprintToRasp = 0 ;
    }
   if(matchFinger > 0)
   {
    matchFinger = 0 ;
    }

   delay(1000);

  //fingerprint identification
  //getFingerprintID();

  //when user ask about one of the sensors (serial.write())
    if (msg == "heartbeat\n") {
      for (int i = 0; i < samp_siz; i++)
       reads[i] = 0;
       sum = 0;
       ptr = 0;
       ht_counter=0;
         while(1)
         {
           if(ht_counter > 10)
           {break;}
           // calculate an average of the sensor
           // during a 20 ms period (this will eliminate
           // the 50 Hz noise caused by electric light
           n = 0;
           start = millis();
           reader = 0.;
           do
           {
             reader += analogRead (heartBit_sensorPin);
             n++;
             now = millis();
           }
           while (now < start + 20);  
           reader /= n;  // we got an average
           // Add the newest measurement to an array
           // and subtract the oldest measurement from the array
           // to maintain a sum of last measurements
           sum -= reads[ptr];
           sum += reader;
           reads[ptr] = reader;
           last = sum / samp_siz;
           // now last holds the average of the values in the array
           // check for a rising curve (= a heart beat)
           if (last > before)
           {
             rise_count++;
             if (!rising && rise_count > rise_threshold)
             {
              ht_counter++;
               // Ok, we have detected a rising curve, which implies a heartbeat.
               // Record the time since last beat, keep track of the two previous
               // times (first, second, third) to get a weighed average.
               // The rising flag prevents us from detecting the same rise 
               // more than once.
               rising = true;
               first = millis() - last_beat;
               last_beat = millis();
               // Calculate the weighed average of heartbeat rate
               // according to the three last beats
               print_value = 60000. / (0.4 * first + 0.3 * second + 0.3 * third);
               sum_heartbeat=sum_heartbeat+print_value;
               //sendData(heartBit_sensorPin,print_value,print_value); //need to change the led_pin we sent
               //Serial.print(print_value);
               //Serial.print('\n');
               third = second;
               second = first;
             }
           }
           else
           {
             // Ok, the curve is falling
             rising = false;
             rise_count = 0;
           }
           before = last;
           ptr++;
           ptr %= samp_siz;
         }
        avg_heartbeat= sum_heartbeat/heartbeat_counter;
    }
    
      if (msg == "Temperature\n") {
    
          while(1){
            // Wait a few seconds between measurements.
            delay(2000);
          
            // Reading temperature or humidity takes about 250 milliseconds!
            // Sensor readings may also be up to 2 seconds 'old' (its a very slow sensor)
            h = dht.readHumidity();
            // Read temperature as Celsius (the default)
            t = dht.readTemperature();
          
            // Check if any reads failed and exit early (to try again).
            //if (isnan(h) || isnan(t) ) {
              //Serial.println(F("Failed to read from DHT sensor!"));
              //return;
            //}
    
         
            //sendData(2,t,h);
          }
          
      }else if(msg=="led0"){
        digitalWrite(ledPin,LOW);
        //Serial.println(" Arduino set led to LOW");
      }else if(msg=="led1"){
        digitalWrite(ledPin,HIGH);
        //Serial.println(" Arduino set led to HIGH");
      }
      delay(500);
    

     if (msg == "panicButton\n") {
        // read the state of the pushbutton value:
        buttonState = digitalRead(buttonPin);
        // Show the state of pushbutton on serial monitor
        //Serial.println(buttonState);
        // check if the pushbutton is pressed.
        // if it is, the buttonState is HIGH:
        if (buttonState == HIGH) {
          // turn LED on:
          //Serial.println("button high");
          //digitalWrite(ledPin, HIGH);
        } else {
          // turn LED off:
          //Serial.println("button low");
          //digitalWrite(ledPin, LOW);
        }
        // Added the delay so that we can see the output of button
        delay(100);       
      } 

  
     if (msg == "medicineSts\n") {
          // here we should take from DB the last time 'medicineMagnetSensorState' has changed and send it to Rasperry pi.
          // client will see the last time and date, X taked medicine 
      } 

  
     if (msg == "addFingerPrint\n") {
          //enroll function
          getFingerprintEnroll();
          //frontrear();

          
      } 


     if (msg == "openDoorLock\n") {
          //fingerprint identification
          getFingerprintID();
          
     } 

      if (msg1 == "deleteFingerPrint") {
          //fingerprint identification
          matchFinger = 5;
          //Serial.println(deletedId);
          first  = atoi (deletedId.substring(0).c_str ());
          //Serial.println(first);
          //matchFinger = deletedId;
          deleteFingerprint(first); // ndde to send ID 
      }
} 


void readSerialPort() {
  msg = "";
  if (Serial.available()) {
    delay(10);
    while (Serial.available() > 0) {
      msg += (char)Serial.read();
    }
    Serial.flush();
  }
}





void task_manager() {
  
  //medcine
  counterForMedicine++;
  medicineMagnetSensorState = digitalRead(medicineMagnetsensorPin);
  //fridge
  counterForFridge++;
  fridgeMagnetSensorState = digitalRead(fridgeMagnetsensorPin);

  if (medicineMagnetSensorState == saveMedicineState){
     //Serial.println("same");
     if (counterForMedicine == 3)
        {
          // X dident take the ball, first, send an email to client.
          medicineMagnetSensorState = 3;
          }

     if (counterForMedicine == 5)
        {
          // X dident take the ball, second, send an email to saved account.
          medicineMagnetSensorState = 5;
          if (medicineMagnetSensorState != saveMedicineState){
            counterForMedicine = 0;
            }
          
          }      
    }
    if (medicineMagnetSensorState != saveMedicineState ){
      //
       // here we can see change in behavior, it means X taked ball today. we sholud send data to DB with hour.
      // takedMedicine++;
     //
       //Serial.println("different");
       saveMedicineState = medicineMagnetSensorState;
      }

  //save the current state
  //saveMedicineState = 0;


  if (fridgeMagnetSensorState == saveFridgeState){
     //Serial.println("same");
     //play buzzer for update X the fridge is open
     if (counterForFridge == 3)
        {
          if (saveFridgeState == 1) //that means all this time fridge was open
          {Serial.println("buzzer");}       
          // X dident open the fridge, first, send an email to client.
          fridgeMagnetSensorState = 3;
          }

     if (counterForFridge == 5)
        {
          // X dident open the fridge, sec, send an email to saved acount.
          fridgeMagnetSensorState = 5;
          if (fridgeMagnetSensorState != saveFridgeState){
            counterForFridge = 0;
            }
          
          }      
    }
    if (fridgeMagnetSensorState != saveFridgeState ){
      //
       // here we can see change in behavior, it means X open the pridge today. we sholud send data to DB with hour.
      // openedFridge++;
     //  
       //Serial.println("different");
       saveFridgeState = fridgeMagnetSensorState;
      }
}




uint8_t getFingerprintEnroll() {

  //Serial.println("Please put your finger on Sensor");
  int p = -1;
  while (p != FINGERPRINT_OK) {
    
    p = finger.getImage();
    
    switch (p) {
    case FINGERPRINT_OK:
      //Serial.println("Image taken");
      break;
    case FINGERPRINT_IMAGEFAIL:
      //Serial.println("Imaging error");
      break;
    }
  }



  p = finger.image2Tz(1);
    switch (p) {
      case FINGERPRINT_OK:
        //Serial.println("Image converted");
        break;
        
      case FINGERPRINT_IMAGEMESS:
        //Serial.println("Image too messy");
        delay(100);
        return p;
        
      case FINGERPRINT_INVALIDIMAGE:
        //Serial.println("Could not find fingerprint features");
        delay(100);
        return p;
  }

  delay(1000);
  //Serial.println("Remove Finger");
  delay(2000);
  p = 0;


  while (p != FINGERPRINT_NOFINGER) {
    p = finger.getImage();
  }

  p = -1;
  
  //Serial.println("Place same finger again");
  
  while (p != FINGERPRINT_OK) {
    p = finger.getImage();
    
    switch (p) {
      
    case FINGERPRINT_OK:
      //Serial.println("Image taken");
      break;
      
    case FINGERPRINT_IMAGEFAIL:
      //Serial.println("Imaging error");
      break;
    }
  }




  p = finger.image2Tz(2);
  
  switch (p) {
    case FINGERPRINT_OK:
      //Serial.println("Image converted");
      break;
      
    case FINGERPRINT_IMAGEMESS:
      //Serial.println("Image too messy");
      delay(100);
      return p;

    case FINGERPRINT_INVALIDIMAGE:
      //Serial.println("Could not find fingerprint features");
      delay(100);
      return p;
  }




  p = finger.createModel();
  
  if (p == FINGERPRINT_OK) {
    //Serial.println("Prints matched!");

  } 
  
  else if (p == FINGERPRINT_PACKETRECIEVEERR) {
    //Serial.println("Communication error");
    delay(100);
    return p;
  } 
  
  else if (p == FINGERPRINT_ENROLLMISMATCH) {
    //Serial.println("Fingerprints did not match");
    delay(100);
    return p;
  } 
  
  else {
    //Serial.println("Unknown error");
    delay(100);
    return p;
  }





  p = finger.storeModel(id);
  if (p == FINGERPRINT_OK) {

    //Serial.println("Stored!");
    frontrear();
    //fungerprintToRasp = id;
    //finger.fingerID = id;
    //id++ ;
  } 
  
  else if (p == FINGERPRINT_PACKETRECIEVEERR) {
   //Serial.println("Communication error");
    delay(100);    
    return p;
  }
  
  else if (p == FINGERPRINT_BADLOCATION) {
    //Serial.println("Could not store in that location");
    delay(100);
    return p;
  } 
  
  else {
    //Serial.println("Unknown error");
    delay(100);
    return p;
  }


  delay(100);
  return true;

}

void frontrear(){
   if(front==-1)
    {
      fungerprintToRasp = id;
      id++;
      //Serial.println("no elements to delete");
    }
    else if (front!= -1)
    {
      fungerprintToRasp= queue[front];
      //Serial.println("the deleted item is:");
      //Serial.println(item);
    }
    else if(front==rear)
    {
      front=-1;
      rear=-1;
    } 
    else
    {
      front++;
    }
  
  }



uint8_t deleteFingerprint(uint8_t id) {
  uint8_t p = -1;
 
  
  p = finger.deleteModel(id);
  if (p == FINGERPRINT_OK) {
    //here addvalue
    if(rear==MAX-1)
    {
      Serial.print("the queue is full");
    }
  
    else
    {
      //Serial.print("enter the element");
      //item = readnumber();
      rear++;
      queue[rear]=id;
      //for(i=front; i<=rear;i++){
        //Serial.println(queue[i]);
        //}
      if(front == -1){
        front=0;
        }   
    }
    //Serial.println("Deleted!");
  } else if (p == FINGERPRINT_PACKETRECIEVEERR) {
    //Serial.println("Communication error");
  } else if (p == FINGERPRINT_BADLOCATION) {
    //Serial.println("Could not delete in that location");
  } else if (p == FINGERPRINT_FLASHERR) {
    //Serial.println("Error writing to flash");
  } else {
    //Serial.print("Unknown error: 0x"); Serial.println(p, HEX);
  }

  return p;
}


//run all time and check if there is an fingerprint identification in DB
uint8_t getFingerprintID() {
  
  uint8_t counter = 0;
      if (counter>500){            
      //Serial.print("No Finger Detected !");
      delay(100);
    }
    
  counter++ ;
  delay(30);
    
  uint8_t p = finger.getImage();
  switch (p) {
    case FINGERPRINT_OK:
      //Serial.println("Image taken");
      break;
    case FINGERPRINT_NOFINGER:
      //Serial.println("No finger detected");
      return p;
    case FINGERPRINT_PACKETRECIEVEERR:
      //Serial.println("Communication error");
      return p;
    case FINGERPRINT_IMAGEFAIL:
      //Serial.println("Imaging error");
      return p;
    default:
      //Serial.println("Unknown error");
      return p;
  }

  // OK success!

  p = finger.image2Tz();
  switch (p) {
    case FINGERPRINT_OK:
      //Serial.println("Image converted");
      break;
    case FINGERPRINT_IMAGEMESS:
      //Serial.println("Image too messy");
      return p;
    case FINGERPRINT_PACKETRECIEVEERR:
      //Serial.println("Communication error");
      return p;
    case FINGERPRINT_FEATUREFAIL:
      //Serial.println("Could not find fingerprint features");
      return p;
    case FINGERPRINT_INVALIDIMAGE:
      //Serial.println("Could not find fingerprint features");
      return p;
    default:
      //Serial.println("Unknown error");
      return p;
  }

  // OK converted!
  p = finger.fingerSearch();
  if (p == FINGERPRINT_OK) {
    //Serial.println("Found a print match!");
    matchFinger = 1;
    fungerprintToRasp = finger.fingerID;
  
  } else if (p == FINGERPRINT_PACKETRECIEVEERR) {
    //Serial.println("Communication error");
    return p;
  } else if (p == FINGERPRINT_NOTFOUND) {
    //Serial.println("Did not find a match");
    matchFinger = 2;
    return p;
  } else {
    //Serial.println("Unknown error");
    return p;
  }

  // found a match!
  //Serial.print("Found ID #"); Serial.print(finger.fingerID);
  //Serial.print(" with confidence of "); Serial.println(finger.confidence);

  return finger.fingerID;
}

// returns -1 if failed, otherwise returns ID #
int getFingerprintIDez() {
  uint8_t p = finger.getImage();
  if (p != FINGERPRINT_OK)  return -1;

  p = finger.image2Tz();
  if (p != FINGERPRINT_OK)  return -1;

  p = finger.fingerFastSearch();
  if (p != FINGERPRINT_OK)  return -1;

  // found a match!
  //Serial.print("Found ID #"); Serial.print(finger.fingerID);
  //Serial.print(" with confidence of "); Serial.println(finger.confidence);
  return finger.fingerID;
}
