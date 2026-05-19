// Sent to BLE_Receiver_Emeka

#include <ArduinoBLE.h>

const int SENSOR_PIN = A4;

BLEService sensorService("181A");
BLEUnsignedIntCharacteristic sensorChar("2A6E", BLERead | BLENotify);

void setup() {
  Serial.begin(9600);
  pinMode(SENSOR_PIN, INPUT);

  if (!BLE.begin()) {
    Serial.println("BLE failed!");
    while (1);
  }

  BLE.setLocalName("SensorNode");
  BLE.setAdvertisedService(sensorService);
  sensorService.addCharacteristic(sensorChar);
  BLE.addService(sensorService);
  sensorChar.writeValue(0);
  BLE.advertise();

  Serial.println("Advertising...");
}

void loop() {
  BLEDevice central = BLE.central();
  if (central) {
    Serial.print("Connected to: ");
    Serial.println(central.address());

    while (central.connected()) {
      unsigned int reading = analogRead(SENSOR_PIN);
      sensorChar.writeValue(reading);
      Serial.print("Sent: ");
      Serial.println(reading);
      delay(500);
    }

    Serial.println("Disconnected.");
  }
}
