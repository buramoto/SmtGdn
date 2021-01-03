//Ethernet library include
#include <SPI.h>
#include <Ethernet.h>
//Include for light sensor
#include <Adafruit_TSL2591.h>

//Network configuration
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
byte ip[] = {192, 168, 10, 20};
byte serverip[] = {192, 168, 10, 17};
int port = 6109;
EthernetClient client;
//int identity = -1;//Set at -1 until we get an id from pi

//Soil sensor settings
int soilPower = 7; //Calibration value for sensor
int soilPin = A0; //Pin read
int soilDataReturn = 0;//Return value for data

//Light sensor settings
Adafruit_TSL2591 tsl = Adafruit_TSL2591(2591);
//sensors_event_t lightSensorEvent;

//Data
struct dataStruct{
  int identity;
  int soilValue;
  int lightValue;
};
dataStruct sensorData = {0, 0, 0}; 

void setup() {
  //Serial
  Serial.begin(9600);
  while(!Serial){
    //Waiting for serial to begin
  }
  Serial.println("Serial port ready");
  
  //Sensor setups
  pinMode(soilPower, OUTPUT);
  tsl.setGain(TSL2591_GAIN_MED);
  tsl.setTiming(TSL2591_INTEGRATIONTIME_400MS);
  Serial.println("Sensor setup ready");
  
  //Ethernet
  Ethernet.init(10);
  Ethernet.begin(mac, ip);
  //Check for shield errors
  if(Ethernet.hardwareStatus() == EthernetNoHardware){
    Serial.println("Problem with ethernet shield");
    while(true){
      delay(1000);
    }
  }
  //Check for ethernet cable
  while (Ethernet.linkStatus() == LinkOFF) {
    Serial.println("Ethernet cable is not connected.");
    delay(500);
  }
  //Begin connection
  Serial.print("Attempting to connect to data station. Connecting to ip address ");
  for(int i = 0; i < 4; i++){
    Serial.print(serverip[i]);
    Serial.print(" ");
  }
  Serial.print(" at port ");
  Serial.println(port);
  while(!client.connected()){//Retry connection until we establish communication with pi
    //wait for connection
    client.connect(serverip, port);
    Serial.println("Attempting to connect...");
    delay(5000);
  }
  Serial.println("Ethernet connection established, retrieving identifier...");
  //We established the connection, now get identifier...
  while(client.available() == 0){
    //Wait for init bytes to come in
  }
  sensorData.identity = client.read();
  Serial.print("Got identifier: ");
  Serial.println(sensorData.identity);
  
  //Init complete
  Serial.println("Arduino initalized. Ready to send data");
}

void loop() {
  delay(5000);
  Serial.println("\nSending data to raspberry pi...");
  sensorData.soilValue = sampleSoilSensor();
  sensorData.lightValue = sampleLightSensor();
  client.write((byte *)&sensorData, sizeof(sensorData));
}

int sampleSoilSensor(){
  int soilMoistureData = 0;
  digitalWrite(soilPower, HIGH);
  delay(10);//Wait for pin to activate
  soilMoistureData = analogRead(soilPin);
  digitalWrite(soilPower, LOW);
  Serial.print("Soil mosture value: ");
  Serial.println(soilMoistureData, DEC);
  return soilMoistureData;
}

int sampleLightSensor(){
  int luxValue = 0;
  sensors_event_t lightSensorEvent;
  tsl.getEvent(&lightSensorEvent);
  luxValue = lightSensorEvent.light;
  Serial.print("Light sensor value: ");
  Serial.println(luxValue);
  return luxValue;
}
