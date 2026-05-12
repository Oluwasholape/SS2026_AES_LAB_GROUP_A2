// Received temperature signal from BLE_Sender_Oluwasholape

#include <ArduinoBLE.h>

void setup() {
  Serial.begin(9600);
  if (!BLE.begin()) while (1);
  BLE.scanForName("SensorNode");
}

void loop() {
  BLEDevice peripheral = BLE.available();

  if (peripheral) {
    BLE.stopScan();
    if (peripheral.connect()) {
      if (peripheral.discoverAttributes()) {
        BLECharacteristic sensorChar = peripheral.characteristic("2A6E");
        if (sensorChar && sensorChar.canRead()) {
          while (peripheral.connected()) {
            sensorChar.read();
            const uint8_t* buf = sensorChar.value();
            unsigned int value = buf[0] | (buf[1] << 8);
            Serial.print("Sensor value: ");
            Serial.println(value);
            delay(500);
          }
        }
      }
      peripheral.disconnect();
    }
    BLE.scanForName("SensorNode");
  }
}
