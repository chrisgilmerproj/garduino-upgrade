//--- Last updated: 2009/11/09

//--- Analog Pins
#define moistureSensor 0
#define lightSensor 1
#define tempSensor 2

//--- Digital Pins
#define lightSwitch 8
#define pumpSwitch 9
#define tempLED 12
#define moistureLED 13

//--- Define serial check bytes as 43 or '+'
#define checkByte1 43
#define checkByte2 43
#define checkByte3 43

//--- Define light and pump commands
#define lightOn 76    // 'L' - Turn the light on
#define waterReset 87 // 'W' - Reset the water cycle counter

//--- Analog value storage
int moisture_val;
int light_val;
int temp_val;

//--- set thresholds
int moisture_thresh = 500;
int temp_thresh = 450;

//--- set light and water information
bool lightIsOn = false;

//--- decide the max number of watering cycles per day
int max_water_cycles = 10;
int current_water_cycles = 0;

void setup(){
  //--- open the serial port
  Serial.begin(19200); 
  
  //--- Set up the LEDs as outputs
  pinMode(moistureLED, OUTPUT);
  pinMode(tempLED, OUTPUT);
  pinMode(lightSwitch, OUTPUT);
  pinMode(pumpSwitch, OUTPUT);
  
  //--- Turn off all the outputs
  digitalWrite(moistureLED,LOW);
  digitalWrite(tempLED,LOW);
  digitalWrite(lightSwitch,LOW);
  digitalWrite(pumpSwitch,LOW);
}

void loop(){
  
  //--- Poll the serial port for instructions
  pollSerialPort();
  
  //--- Manage the garden
  manageGarden();
  
  //--- Send data out over the serial port
  sendData();
  
}

void pollSerialPort(){
  
  //--- This variable will hold data from the serial port
  int data;
  
  //--- Check to see if the buffer has enough data to process
  if(Serial.available() >= 5){
    data = Serial.read();
    //Serial.print(data);
    //--- Check the first byte
    if(data = checkByte1){
      data = Serial.read();
      //Serial.print(data);
      //--- Check the second byte
      if(data = checkByte2){
        data = Serial.read();
        //Serial.print(data);
        //--- Check the third byte
        if(data = checkByte3){
          //--- The fourth byte gives information about the light
          int lightChar = Serial.read();
          
          //--- Determine if the light should be on or off
          if(lightChar == lightOn){
            lightIsOn = true;
          } else {
            lightIsOn = false;
          }
          
          //--- The fifth byte tells us to reset the water cycle counter
          int waterChar = Serial.read(); 
          
          //--- Reset the water cycle counter
          if(waterChar == waterReset){
            current_water_cycles = 0;
          }
        }
      }
    }
  }
}

//--- Turn the lights and pumps on and off, also get the data values for each sensor
void manageGarden(){
  
  //##########################################################
  //--- read the value from the light sensing probe
  //    High light values are dark, low light values are bright
  light_val = analogRead(lightSensor);
  
  //--- turn lights on if the hours is correct
  if (lightIsOn)
  {
    digitalWrite(lightSwitch, HIGH);
  }
  
  //--- turn off lights
  else
  {
    digitalWrite(lightSwitch, LOW);
  }
  
  //##########################################################
  //--- read the value from the temperature sensing probe
  temp_val = analogRead(tempSensor);
  
  //--- If the temperature is too low then light an LED
  //    High temp values are cold, low temp values are hot
  if(temp_val < temp_thresh){
    digitalWrite(tempLED, HIGH);  // set the LED on
  } else {
    digitalWrite(tempLED, LOW);   // set the LED on
  }
  
  //##########################################################
  //--- read the value from the moisture sensing probe
  moisture_val = analogRead(moistureSensor); 

  //--- If the moisture is too low then light an LED
  //    Low moisture values are dry, high moisture values are wet
  while(moisture_val < moisture_thresh and current_water_cycles < max_water_cycles){
    digitalWrite(pumpSwitch, HIGH);   // turn on the pump
    digitalWrite(moistureLED, HIGH);  // set the LED on
    delay(5000);                     // wait for 5 seconds
    moisture_val = analogRead(moistureSensor); // read in the moisture value again
    
    //--- Quit this after 25 seconds
    current_water_cycles = current_water_cycles + 1;
  } 
  
  //--- Turn off the pump
  digitalWrite(pumpSwitch, LOW);    // turn off the pump
  digitalWrite(moistureLED, LOW);   // set the LED off
  
}

//--- Send data back over serial
void sendData(){
  Serial.print("light_sensor: ");
  Serial.print(light_val);
  Serial.print(";temp_sensor: ");
  Serial.print(temp_val);
  Serial.print(";moisture_sensor: ");
  Serial.print(moisture_val);
  Serial.print(";\n");
  
  delay(10000);
}
