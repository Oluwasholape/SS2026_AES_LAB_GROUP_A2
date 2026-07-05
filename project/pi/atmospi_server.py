#!/usr/bin/env python3
"""
AtmosPi server — runs on the Raspberry Pi 3 Model B, next to the Mosquitto broker.

One process, four jobs:
  1. MQTT client  — subscribes to atmospi/# on the local Mosquitto broker and
                    keeps the latest reading of every node in memory.
  2. Storage      — appends every reading to a SQLite database so history
                    survives restarts and can be exported as CSV.
  3. Alarm logic  — evaluates each node's readings against safety thresholds
                    and assigns a severity level (normal/warning/critical/
                    offline). This runs here, not in the browser, in line with
                    the lab's own guidance: "the more you implement for
                    visualization on Pi-side the better."
  4. Web server   — Flask serves the live dashboard (responsive: desktop and
                    mobile) plus a small JSON API used by the dashboard.

Everything is served from the Pi itself: no CDNs, no cloud services, no paid
accounts. Any device on the Tailscale VPN can open http://<pi-tailscale-ip>:8080

Run manually:      python3 atmospi_server.py
Run as a service:  see systemd/atmospi.service
"""

import json
import sqlite3
import threading
import time
from pathlib import Path

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template, request, Response

# --------------------------------------------------------------- settings --
BROKER_HOST = "localhost"          # Mosquitto runs on this same Pi
BROKER_PORT = 1883
HTTP_PORT   = 8080
DB_PATH     = Path(__file__).with_name("atmospi.db")
ONLINE_WINDOW_S = 10               # node counts as online if seen in last 10 s

# Node metadata used by the dashboard (id -> label, physical zone, network)
NODES = {
    "node1": {"label": "Node 1 · Climate",   "sensor": "KY-015 DHT11",
              "zone": "Hallway L3 — desk A", "metrics": ["temp_c", "hum_pct", "light_pct"]},
    "node2": {"label": "Node 2 · Precision", "sensor": "KY-001 DS18B20",
              "zone": "Hallway L3 — desk B", "metrics": ["temp_c", "light_pct"]},
    "node3": {"label": "Node 3 · Analog",    "sensor": "KY-013 NTC",
              "zone": "Hallway L3 — desk C", "metrics": ["temp_c", "light_pct"]},
}
METRICS = {
    "temp_c":    {"label": "Temperature", "unit": "°C"},
    "hum_pct":   {"label": "Humidity",    "unit": "%"},
    "light_pct": {"label": "Light level", "unit": "%"},
}

# ---------------------------------------------------------- alarm logic --
# Thresholds are deliberately loose enough to trigger live during a demo
# (cup your hand around the DHT11 for warmth, breathe on it for humidity,
# cover the KY-018 for darkness) while still reading as a plausible
# industrial-safety policy: out-of-range temperature/humidity flags an
# HVAC or process fault, and loss of illumination is a safety hazard in a
# monitored work zone. A node that has gone silent is always "offline"
# regardless of its last known values.
ALARM_THRESHOLDS = {
    "temp_c":    {"warn_high": 27, "crit_high": 32, "warn_low": 12, "crit_low": 8},
    "hum_pct":   {"warn_high": 65, "crit_high": 80, "warn_low": 25, "crit_low": 15},
    "light_pct": {"warn_low": 25, "crit_low": 10},   # no upper-bound alarm
}
ALARM_RANK = {"normal": 0, "warning": 1, "critical": 2, "offline": 3}


def compute_alarm(metrics, online):
    """Return 'normal' | 'warning' | 'critical' | 'offline' for one node."""
    if not online:
        return "offline"

    level = "normal"
    for metric, value in metrics.items():
        th = ALARM_THRESHOLDS.get(metric)
        if not th:
            continue
        node_level = "normal"
        if ("crit_high" in th and value >= th["crit_high"]) or \
           ("crit_low" in th and value <= th["crit_low"]):
            node_level = "critical"
        elif ("warn_high" in th and value >= th["warn_high"]) or \
             ("warn_low" in th and value <= th["warn_low"]):
            node_level = "warning"
        if ALARM_RANK[node_level] > ALARM_RANK[level]:
            level = node_level
    return level


# ------------------------------------------------------------------ state --
state_lock = threading.Lock()
latest = {}          # node -> {"ts": float, "metrics": {name: value}}
gateway_status = {"value": "unknown", "ts": 0.0}
msg_count = 0
started_at = time.time()

# ---------------------------------------------------------------- storage --
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS readings(
                      ts REAL NOT NULL, node TEXT NOT NULL,
                      metric TEXT NOT NULL, value REAL NOT NULL)""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_r
                    ON readings(node, metric, ts)""")
    return conn


def store(ts, node, metrics):
    conn = db()
    conn.executemany("INSERT INTO readings VALUES (?,?,?,?)",
                     [(ts, node, m, v) for m, v in metrics.items()])
    conn.commit()
    conn.close()

# ------------------------------------------------------------------- mqtt --
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"[mqtt] connected to broker ({reason_code}); subscribing atmospi/#")
    client.subscribe("atmospi/#")


def on_message(client, userdata, msg):
    global msg_count
    now = time.time()
    parts = msg.topic.split("/")            # atmospi/<node>/data
    if len(parts) < 3:
        return

    if parts[1] == "gateway" and parts[2] == "status":
        with state_lock:
            gateway_status["value"] = msg.payload.decode("utf-8", "ignore")
            gateway_status["ts"] = now
        return

    if parts[2] != "data":
        return
    try:
        payload = json.loads(msg.payload.decode("utf-8", "ignore"))
    except json.JSONDecodeError:
        return

    node = payload.get("node", parts[1])
    values = {k: float(v) for k, v in payload.items()
              if k in METRICS and isinstance(v, (int, float))}
    if not values:
        return

    with state_lock:
        entry = latest.setdefault(node, {"ts": 0, "metrics": {}})
        entry["ts"] = now
        entry["metrics"].update(values)
        msg_count += 1
    store(now, node, values)


def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id="atmospi-server")
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(1, 10)
    client.connect_async(BROKER_HOST, BROKER_PORT, keepalive=30)
    client.loop_start()
    return client

# ------------------------------------------------------------------ flask --
app = Flask(__name__)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/latest")
def api_latest():
    now = time.time()
    with state_lock:
        nodes = {}
        summary = {"normal": 0, "warning": 0, "critical": 0, "offline": 0}
        for nid, meta in NODES.items():
            entry = latest.get(nid)
            online = bool(entry and now - entry["ts"] <= ONLINE_WINDOW_S)
            metrics = entry["metrics"] if entry else {}
            alarm = compute_alarm(metrics, online)
            summary[alarm] += 1
            nodes[nid] = {
                "label": meta["label"], "sensor": meta["sensor"],
                "zone": meta["zone"],
                "online": online,
                "age_s": round(now - entry["ts"], 1) if entry else None,
                "metrics": metrics,
                "alarm": alarm,
            }
        gw_online = (gateway_status["value"] == "online")
        payload = {
            "nodes": nodes,
            "summary": summary,
            "gateway": {"online": gw_online, "status": gateway_status["value"]},
            "server": {"uptime_s": int(now - started_at),
                       "messages": msg_count,
                       "time": time.strftime("%H:%M:%S")},
            "metrics_meta": METRICS,
        }
    return jsonify(payload)


@app.route("/api/history")
def api_history():
    minutes = min(int(request.args.get("minutes", 30)), 24 * 60)
    since = time.time() - minutes * 60
    conn = db()
    rows = conn.execute(
        "SELECT ts, node, metric, value FROM readings WHERE ts >= ? ORDER BY ts",
        (since,)).fetchall()
    conn.close()

    series = {}
    for ts, node, metric, value in rows:
        series.setdefault(node, {}).setdefault(metric, []).append(
            [round(ts, 1), value])

    # Downsample so the browser never receives more than ~300 pts per line
    for node in series:
        for metric, pts in series[node].items():
            if len(pts) > 300:
                step = len(pts) / 300.0
                series[node][metric] = [pts[int(i * step)] for i in range(300)]
    return jsonify({"minutes": minutes, "series": series})


@app.route("/api/export.csv")
def api_export():
    conn = db()
    rows = conn.execute(
        "SELECT ts, node, metric, value FROM readings ORDER BY ts").fetchall()
    conn.close()

    def gen():
        yield "timestamp,iso_time,node,metric,value\n"
        for ts, node, metric, value in rows:
            iso = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
            yield f"{ts:.1f},{iso},{node},{metric},{value}\n"

    return Response(gen(), mimetype="text/csv",
                    headers={"Content-Disposition":
                             "attachment; filename=atmospi_readings.csv"})


if __name__ == "__main__":
    start_mqtt()
    print(f"[http] dashboard on http://0.0.0.0:{HTTP_PORT}")
    app.run(host="0.0.0.0", port=HTTP_PORT, threaded=True)
