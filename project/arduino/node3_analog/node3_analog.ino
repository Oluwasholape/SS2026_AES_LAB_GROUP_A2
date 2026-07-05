/*
 * AtmosPi — Node 3 "analog"
 * Sensors: KY-013 (NTC thermistor, analog temperature) + KY-018 (photoresistor)
 * Board:   Arduino UNO WiFi Rev2
 *
 * The KY-013 gives us a third, fully analog temperature measurement so the
 * dashboard can compare three sensing technologies side by side:
 * DHT11 (digital combo, node1) vs DS18B20 (1-Wire, node2) vs NTC (analog, node3).
 * Temperature is derived from the ADC value with the Steinhart-Hart equation.
 *
 * Output:  one JSON line every SAMPLE_MS on the USB serial port, e.g.
 *          {"node":"node3","temp_c":22.7,"light_pct":61,"light_raw":364}
 *
 * Wiring (no breadboard):
 *   KY-013  S (signal)     -> A1
 *   KY-013  middle pin     -> 5V
 *   KY-013  - (GND)        -> GND
 *     NOTE: on some KY-013 clones the silkscreen for S and - is swapped.
 *     If you read a constant/absurd temperature, swap the S and - jumpers.
 *   KY-018  S              -> A0
 *   KY-018  middle pin     -> 5V
 *   KY-018  -              -> GND
 *
 * Libraries: none required (plain analogRead + math).
 */

#include <math.h>

#define NODE_ID      "node3"
#define NTC_PIN      A1
#define LDR_PIN      A0
#define SAMPLE_MS    2000UL
#define LIGHT_INVERT 0

unsigned long lastSample = 0;

float readThermistorC() {
  // Average a few samples to calm ADC noise
  long acc = 0;
  for (byte i = 0; i < 8; i++) { acc += analogRead(NTC_PIN); delay(2); }
  float raw = acc / 8.0;
  if (raw <= 0 || raw >= 1023) return NAN;

  // KY-013: 10k NTC + 10k fixed resistor divider
  float r = 10000.0 * (1023.0 / raw - 1.0);

  // Steinhart-Hart with standard coefficients for the 10k NTC
  float lnR = log(r);
  float tK = 1.0 / (0.001129148 + 0.000234125 * lnR
                    + 0.0000000876741 * lnR * lnR * lnR);
  return tK - 273.15;
}

void setup() {
  Serial.begin(9600);
}

void loop() {
  unsigned long now = millis();
  if (now - lastSample < SAMPLE_MS) return;
  lastSample = now;

  float t = readThermistorC();

  int raw = analogRead(LDR_PIN);
  int pct = map(raw, 0, 1023, 0, 100);
  if (LIGHT_INVERT) pct = 100 - pct;

  Serial.print(F("{\"node\":\"" NODE_ID "\""));
  if (!isnan(t) && t > -30 && t < 80) { Serial.print(F(",\"temp_c\":")); Serial.print(t, 1); }
  Serial.print(F(",\"light_pct\":")); Serial.print(pct);
  Serial.print(F(",\"light_raw\":")); Serial.print(raw);
  Serial.println(F("}"));
}
