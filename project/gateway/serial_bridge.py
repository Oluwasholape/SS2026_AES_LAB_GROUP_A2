#!/usr/bin/env python3
"""
AtmosPi gateway — serial-to-MQTT bridge.

Runs on the Windows laptop in the L3 hallway. Opens the USB serial port of
each of the three Arduino sensor nodes, reads the JSON line each node prints
every ~2 s, and republishes it to the Mosquitto broker on the Raspberry Pi
over the Tailscale VPN.

IMPORTANT: close every Arduino IDE Serial Monitor before starting this
script. Windows gives exclusive access to a COM port, so the bridge and the
IDE monitor cannot read the same port at the same time. This script prints
the live feed itself, so it doubles as the "serial monitor" for the demo.

Usage:
    1) copy config.example.json -> config.json and edit it
    2) pip install -r requirements.txt
    3) python serial_bridge.py
"""

import json
import sys
import time
import threading
from pathlib import Path

import serial                      # pyserial
from serial.tools import list_ports
import paho.mqtt.client as mqtt

CONFIG_PATH = Path(__file__).with_name("config.json")

# ---------------------------------------------------------------- config --
def load_config():
    if not CONFIG_PATH.exists():
        sys.exit("config.json not found. Copy config.example.json to "
                 "config.json and fill in the Pi's Tailscale IP + COM ports.")
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def autodetect_ports():
    """List candidate Arduino COM ports (used when config ports are empty)."""
    found = []
    for p in list_ports.comports():
        desc = (p.description or "").lower()
        if "arduino" in desc or "usb serial" in desc or "usb-serial" in desc:
            found.append(p.device)
    return found


# ------------------------------------------------------------------ mqtt --
def make_mqtt(cfg):
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="atmospi-gateway",
    )
    # Last Will: broker tells everyone if the gateway drops off the network
    client.will_set("atmospi/gateway/status", "offline", qos=1, retain=True)

    def on_connect(c, userdata, flags, reason_code, properties):
        print(f"[mqtt] connected to {cfg['broker_host']}:{cfg['broker_port']} "
              f"({reason_code})")
        c.publish("atmospi/gateway/status", "online", qos=1, retain=True)

    def on_disconnect(c, userdata, flags, reason_code, properties):
        print(f"[mqtt] disconnected ({reason_code}), auto-reconnecting ...")

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=10)
    client.connect_async(cfg["broker_host"], cfg["broker_port"], keepalive=30)
    client.loop_start()
    return client


# ---------------------------------------------------------------- serial --
def port_reader(port, cfg, client, stats):
    """One thread per Arduino: read JSON lines, publish to MQTT, forever."""
    while True:
        try:
            with serial.Serial(port, cfg.get("baud", 9600), timeout=5) as ser:
                print(f"[{port}] open")
                ser.reset_input_buffer()
                while True:
                    line = ser.readline().decode("utf-8", "ignore").strip()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                        node = payload.get("node")
                        if not node:
                            continue
                    except json.JSONDecodeError:
                        continue        # partial line at startup etc.

                    topic = f"atmospi/{node}/data"
                    client.publish(topic, line, qos=0)
                    stats[node] = stats.get(node, 0) + 1
                    print(f"[{port}] {node:>5} #{stats[node]:<5} -> {topic}  {line}")
        except (serial.SerialException, OSError) as e:
            print(f"[{port}] serial error: {e} — retrying in 3 s")
            time.sleep(3)


# ------------------------------------------------------------------ main --
def main():
    cfg = load_config()
    ports = cfg.get("serial_ports") or autodetect_ports()
    if not ports:
        sys.exit("No serial ports configured and none auto-detected. "
                 "Plug the Arduinos in and list ports with: "
                 "python -m serial.tools.list_ports")

    print("AtmosPi gateway starting")
    print(f"  broker : {cfg['broker_host']}:{cfg['broker_port']} (via Tailscale)")
    print(f"  ports  : {', '.join(ports)}")
    print("  Ctrl+C to stop\n")

    client = make_mqtt(cfg)
    stats = {}
    for port in ports:
        t = threading.Thread(target=port_reader,
                             args=(port, cfg, client, stats), daemon=True)
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nstopping ...")
        client.publish("atmospi/gateway/status", "offline", qos=1, retain=True)
        time.sleep(0.5)
        client.loop_stop()


if __name__ == "__main__":
    main()
