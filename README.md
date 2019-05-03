# LoRa Sense 
A wireless sensor network using LoRa, implemented for the Advanced Networks module at University of Southampton

## Network architecture

A star network topology is used, with a LoPy acting as the basestation. The nodes are Raspberry Pi 3Bs (equipped with the Dragino LoRa/GPS Hat) that are paired with a Nordic Thingy:52 (via Bluetooth LE) to collect geotagged, timestamped environmental sensor data. 

Only a single node has been tested/demonstrated but the network protocol has capacity for an arbitrary number of nodes.

## Equipment used

- PyCom LoPy 1.0
- Raspberry Pi model 3B
- Dragino LoRa GPS Hat (Hope RF95 with SX1276 transceiver)
- Nordic Thingy:52 (https://www.nordicsemi.com/Software-and-Tools/Development-Kits/Nordic-Thingy-52)

## Setup

### Raspberry Pi Node
A Raspberry Pi 3B was used to connect to a Nordic Thingy 52 forming the nodes on the network. The Pi Zero is equipped with Bluetooth LE meaning it is capable of communicating with the Thingy.

The python `bluepy` library was used for communications. The following tutorials helped:
https://www.elinux.org/RPi_Bluetooth_LE
https://stackoverflow.com/questions/32947807/cannot-connect-to-ble-device-on-raspberry-pi


### Dragino LoRa/GPS Hat with TTN

Roughly follow these steps: http://wiki.dragino.com/index.php?title=Connect_to_TTN#Use_LoRa_GPS_HAT_and_RPi_3_as_LoRa_End_Device

1. Add new device on TTN portal
2. Choose ABP authentication
3. Generate APP/DEV/NSK keys
4. Use the 'thingsnetwork-send-v1' example from this repo https://github.com/dragino/lmic_pi/archive/master.zip
5. Find config.h and uncomment the define directive for EU868, and comment the US961 one.
6. Update the define directives for the DEV_ADDR, ARTKEY, etc. in the thingsnetwork-send-v1 file.
7. Compile and run the file above

## Network Protocol

Each node in the network has a 1-byte ID, with the basestation addressed as 0. Nodes request to join the network, and the basestation tracks all known nodes. Nodes receive their ID as a command-line parameter to simplify the protocol, so it is up to the person starting the network to ensure there are no naming collisions. 

### Packet structure

Packet headers are as follows:

| Byte 0 | 1       | 2        | 3       | ...     |
|--------|---------|----------|---------|---------|
| src ID | dest ID | msg type | payload | payload |

The message type can be any of:
- JOIN_REQUEST (value 0): sent from an (unknown) node to the basestation to request membership to the network
- JOIN_ACK (value 1): sent from the basestation to a newly accepted node to confirm membership
- SENSOR_RESPONSE (value 2): a packet containing geotagged sensor data as requested by the basestation
- SENSOR_REQUEST (value 3): a request made by the basestation to a node for sensor data of a particular type

### Payload structure

The structure of the payload for each message type is as follows:

JOIN_REQUEST:

The payload sent by the node contains information about the sensors it has available to it, so that the basestation can decide which data to request. 4 bytes are used for the 4 supported sensors (temperature, humidity, air quality {CO2 and TVOC}, and pressure). Each byte is 1 for available or 0 for unavailable. Note: this could be optimised to use a single byte with bit-flags.

| Byte | 0               | 1                | 2                   | 3                |
|------|-----------------|------------------|---------------------|------------------|
| Item | temp. available | humid. available | air qual. available | press. available | 


JOIN_RESPONSE:

The payload is a single byte of value 0.

| Byte | 0               | 
|------|-----------------|
| Item | 0               | 

SENSOR_REQUEST:

The basestation requests a single sensor data item, so the payload here includes which data is needed to be sent back. The sensor type is a number 0-4 encoded as ASCII. 

| Byte | 0                | 
|------|------------------|
| Item | Sensor type (0-4)| 

SENSOR_RESPONSE:

The node returns sensor data, with the payload containing the result. Most sensor types return a single byte but air quality returns two bytes (CO2 and TVOC).

| Byte | 0                | 1                |
|------|------------------|------------------|
| Item | Sensor data      | More sensor data |
