#include <ArduinoBLE.h>

const char* targetSvc = "181A";
const char* targetMetric = "2A6E";

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  Serial.begin(9600);
  delay(2000);
  if (!BLE.begin()) {
    while (1) {
      digitalWrite(LED_BUILTIN, HIGH); delay(100);
      digitalWrite(LED_BUILTIN, LOW);  delay(100);
    }
  }
  BLE.scanForUuid(targetSvc);
  digitalWrite(LED_BUILTIN, HIGH);
}

void loop() {
  BLEDevice node = BLE.available();
  if (node) {
    if (node.localName() != "Device_Monitor") {
      return;
    }
    BLE.stopScan();
    processNode(node);
    BLE.scanForUuid(targetSvc);
    digitalWrite(LED_BUILTIN, HIGH);
  }
}

void processNode(BLEDevice node) {
  if (!node.connect()) return;
  digitalWrite(LED_BUILTIN, LOW);
  if (!node.discoverAttributes()) {
    node.disconnect();
    return;
  }
  BLECharacteristic attr = node.characteristic(targetMetric);
  if (!attr || !attr.canSubscribe()) {
    node.disconnect();
    return;
  }
  attr.subscribe();
  while (node.connected()) {
    if (attr.valueUpdated()) {
      int16_t val = 0;
      attr.readValue(val);
      Serial.print(val / 100);
      Serial.print(".");
      int frac = val % 100;
      if (frac < 10) Serial.print("0");
      Serial.println(frac);
      digitalWrite(LED_BUILTIN, HIGH); delay(20);
      digitalWrite(LED_BUILTIN, LOW);
    }
  }
}
