/*
 * AtmosPi — Node 1 "climate"
 * Sensors: KY-015 (DHT11, temperature + relative humidity) + KY-018 (photoresistor)
 * Board:   Arduino UNO WiFi Rev2
 *
 * Output:  one JSON line every SAMPLE_MS on the USB serial port, e.g.
 *          {"node":"node1","temp_c":22.4,"hum_pct":41.0,"light_pct":63,"light_raw":378}
 *          The gateway (serial_bridge.py) forwards each line to the MQTT broker
 *          on the Raspberry Pi over the Tailscale VPN.
 *
 * Wiring (no breadboard — three female-female jumpers straight to the module):
 *   KY-015  S (left pin)   -> D2
 *   KY-015  middle pin     -> 5V
 *   KY-015  - (right pin)  -> GND
 *   KY-018  S              -> A0
 *   KY-018  middle pin     -> 5V
 *   KY-018  -              -> GND
 *
 * Libraries (Arduino IDE -> Tools -> Manage Libraries):
 *   "DHT sensor library" by Adafruit  (installs "Adafruit Unified Sensor" with it)
 */

#include <DHT.h>

#define NODE_ID     "node1"
#define DHT_PIN     2
#define DHT_TYPE    DHT11        // KY-015 carries a DHT11
#define LDR_PIN     A0
#define SAMPLE_MS   2000UL

// KY-018 divider: more light -> lower LDR resistance -> HIGHER voltage on S.
// If your module reads inverted, set LIGHT_INVERT to 1.
#define LIGHT_INVERT 0

DHT dht(DHT_PIN, DHT_TYPE);
unsigned long lastSample = 0;

void setup() {
  Serial.begin(9600);
  dht.begin();
}

void loop() {
  unsigned long now = millis();
  if (now - lastSample < SAMPLE_MS) return;
  lastSample = now;

  float t = dht.readTemperature();   // Celsius
  float h = dht.readHumidity();      // %RH

  int raw = analogRead(LDR_PIN);     // 0..1023
  int pct = map(raw, 0, 1023, 0, 100);
  if (LIGHT_INVERT) pct = 100 - pct;

  // DHT11 occasionally returns NaN — skip the climate fields for that cycle
  Serial.print(F("{\"node\":\"" NODE_ID "\""));
  if (!isnan(t)) { Serial.print(F(",\"temp_c\":"));  Serial.print(t, 1); }
  if (!isnan(h)) { Serial.print(F(",\"hum_pct\":")); Serial.print(h, 1); }
  Serial.print(F(",\"light_pct\":")); Serial.print(pct);
  Serial.print(F(",\"light_raw\":")); Serial.print(raw);
  Serial.println(F("}"));
}
