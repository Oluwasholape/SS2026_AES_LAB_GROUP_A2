/*
 * AtmosPi — Node 2 "precision"
 * Sensors: KY-001 (DS18B20 digital 1-Wire thermometer, ±0.5 °C) + KY-018 (photoresistor)
 * Board:   Arduino UNO WiFi Rev2
 *
 * Output:  one JSON line every SAMPLE_MS on the USB serial port, e.g.
 *          {"node":"node2","temp_c":21.94,"light_pct":58,"light_raw":347}
 *
 * Wiring (no breadboard; the KY-001 module already has the 4.7 kOhm
 * 1-Wire pull-up resistor on board):
 *   KY-001  S (signal)     -> D2
 *   KY-001  middle pin     -> 5V
 *   KY-001  - (GND)        -> GND
 *   KY-018  S              -> A0
 *   KY-018  middle pin     -> 5V
 *   KY-018  -              -> GND
 *
 * Libraries (Arduino IDE -> Tools -> Manage Libraries):
 *   "OneWire" by Paul Stoffregen
 *   "DallasTemperature" by Miles Burton
 */

#include <OneWire.h>
#include <DallasTemperature.h>

#define NODE_ID      "node2"
#define ONE_WIRE_PIN 2
#define LDR_PIN      A0
#define SAMPLE_MS    2000UL
#define LIGHT_INVERT 0

OneWire oneWire(ONE_WIRE_PIN);
DallasTemperature ds18b20(&oneWire);
unsigned long lastSample = 0;

void setup() {
  Serial.begin(9600);
  ds18b20.begin();
  ds18b20.setResolution(12);       // 0.0625 degC steps
}

void loop() {
  unsigned long now = millis();
  if (now - lastSample < SAMPLE_MS) return;
  lastSample = now;

  ds18b20.requestTemperatures();
  float t = ds18b20.getTempCByIndex(0);   // DEVICE_DISCONNECTED_C = -127 on error

  int raw = analogRead(LDR_PIN);
  int pct = map(raw, 0, 1023, 0, 100);
  if (LIGHT_INVERT) pct = 100 - pct;

  Serial.print(F("{\"node\":\"" NODE_ID "\""));
  if (t > -100.0) { Serial.print(F(",\"temp_c\":")); Serial.print(t, 2); }
  Serial.print(F(",\"light_pct\":")); Serial.print(pct);
  Serial.print(F(",\"light_raw\":")); Serial.print(raw);
  Serial.println(F("}"));
}
