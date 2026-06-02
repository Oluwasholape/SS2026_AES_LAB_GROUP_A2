# SS2026_AES_Lab_Group_A2

Advanced Embedded Systems Lab - SS2026
Hochschule Hamm-Lippstadt

## Team Members
- Boiddo, Sumon
- Nnachi-Egwu, Nnaemeka
- Oyemade, Oluwasholape Daniel
- Tuhin, Md Tawhidur Rahman

## Hardware Required for project (as requested by Ali Alhalabi)
| Item | Qty | Role / Notes |
|---|---|---|
| Raspberry Pi 4 (2 GB+) | 1 | MQTT broker (Mosquitto), web server, dashboard host |
| Arduino Uno WiFi Rev2 | 3 | Sensor nodes, one per monitoring zone |
| DHT22 | 3 | Temperature (°C) and relative humidity (%), one per node |
| MQ-135 | 2 | Air quality / CO2 / VOC levels, nodes 1 and 2 |
| BH1750 | 3 | Ambient light level (lux) over I2C, one per node |
| MicroSD Card (32 GB) | 1 | Raspberry Pi OS and data persistence |
| Half-size Breadboard | 3 | Per-node prototyping |
| Jumper wires and resistors | | 10 kOhm pull-ups for DHT22, general wiring |

Full project sketch can be found in the [project](https://github.com/Oluwasholape/SS2026_AES_LAB_GROUP_A2/tree/main/project) directory

## Repository Structure
- [labs](https://github.com/Oluwasholape/SS2026_AES_LAB_GROUP_A2/tree/main/labs): Arduino UNO lab exercises
- [project](https://github.com/Oluwasholape/SS2026_AES_LAB_GROUP_A2/tree/main/project): Final project files
