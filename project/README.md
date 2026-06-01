# Documentation
**Team Name:** Team A2  
**Date:** 19.05.2026

---

## Team Members
* **Boiddo, Sumon** 
* **Nnachi-Egwu Nnaemeka** 
* **Oyemade, Oluwasholape Daniel**  
* **Tuhin, Md Tawhidur Rahman** 

---

## 1. Introduction
The project focuses on the design and development of a Smart Agriculture Monitoring and Irrigation System using Industrial Internet of Things (IIoT) technologies. The system combines embedded systems, wireless sensor networks, and industrial communication standards to monitor environmental conditions and automate irrigation processes.

The project aims to improve water efficiency, monitoring capability, scalability, and reliability in agricultural environments. Wireless sensor nodes collect data such as soil moisture, temperature, and humidity, which is transmitted to a monitoring platform through MQTT communication.


## 2. Concept Description
Target Application:
The system is designed for smart agriculture environments where continuous monitoring of soil and environmental conditions is required.

Main Application:
Automated irrigation and environmental monitoring.

Main Components:
- ESP32 microcontroller
- Soil moisture sensor
- DHT22 temperature and humidity sensor
- Relay module
- Water pump
- MQTT broker
- Dashboard platform (Node-RED / ThingsBoard)

Initial System Architecture:

Sensors → ESP32 → MQTT Protocol → MQTT Broker → Dashboard → Irrigation Control


## 3. Project / Team Management
Project Method:
The project follows a collaborative engineering workflow using GitHub for version control and task management.

Task Breakdown:
• Hardware integration
• Embedded programming
• MQTT communication setup
• Dashboard implementation
• Documentation and validation

Team Roles:
• Boiddo, Sumon: Hardware and sensors
• Nnachi-Egwu Nnaemeka: Embedded software development
• Oyemade, Oluwasholape Daniel: MQTT communication and dashboard
• Tuhin, Md Tawhidur Rahman: Documentation, testing, and validation


## 4. Technologies
Sensors:
• DHT22 temperature and humidity sensor
• Capacitive soil moisture sensor

Communication Protocol:
• MQTT (Message Queuing Telemetry Transport)

Programming Languages:
• C/C++ for ESP32 programming
• Python/JavaScript for dashboard integration (optional)

Development Tools:
• Arduino IDE / PlatformIO
• Mosquitto MQTT Broker
• GitHub


## 5. Implementation
Static Structure:
The system consists of distributed sensor nodes connected to an ESP32 microcontroller. The ESP32 processes sensor data and publishes the data using MQTT communication.

Main Modules:
• Sensor acquisition module
• MQTT communication module
• Irrigation control module
• Dashboard visualization module

Use Cases:
• Monitor soil moisture levels
• Display environmental conditions
• Automatically activate irrigation
• Log and analyze sensor data


## 6. Results
Expected Results:
• Real-time monitoring of environmental conditions
• Reliable MQTT-based communication
• Automated irrigation control
• Dashboard visualization of sensor values
• Scalable architecture for additional sensor nodes

Planned Validation:
• Communication latency testing
• Reliability testing
• Sensor response verification
• Irrigation trigger testing


## 7. Sources / References
