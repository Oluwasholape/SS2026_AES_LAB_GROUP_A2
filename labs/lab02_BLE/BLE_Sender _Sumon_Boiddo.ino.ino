#include <ArduinoBLE.h>
#include <OneWire.h>

#define PROTOCOL_PIN 2
OneWire protocol(PROTOCOL_PIN);

BLEService svc("181A");
BLEShortCharacteristic metric("2A6E", BLERead | BLENotify);

unsigned long prevTime = 0;
const unsigned long interval = 1000;

int16_t fetchValue() {
  byte buffer[9];
  protocol.reset();
  protocol.skip();
  protocol.write(0x44, 0);
  delay(750);
  protocol.reset();
  protocol.skip();
  protocol.write(0xBE);
  for (byte i = 0; i < 9; i++) buffer[i] = protocol.read();
  int16_t raw = (buffer[1] << 8) | buffer[0];
  return (int16_t)(((int32_t)raw * 25) / 4);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  if (!BLE.begin()) {
    while (1) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(100);
      digitalWrite(LED_BUILTIN, LOW);
      delay(100);
    }
  }
  BLE.setLocalName("Device_Monitor");
  BLE.setDeviceName("Device_Monitor");
  BLE.setAdvertisedService(svc);
  svc.addCharacteristic(metric);
  BLE.addService(svc);
  metric.writeValue((int16_t)0);
  BLE.advertise();
  digitalWrite(LED_BUILTIN, HIGH);
}

void loop() {
  BLEDevice link = BLE.central();
  if (link) {
    while (link.connected()) {
      if (millis() - prevTime >= interval) {
        prevTime = millis();
        metric.writeValue(fetchValue());
        digitalWrite(LED_BUILTIN, LOW);
        delay(20);
        digitalWrite(LED_BUILTIN, HIGH);
      }
    }
  }
}
