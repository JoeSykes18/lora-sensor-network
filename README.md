# LoRa Sense 
A wireless sensor network using LoRa, implemented for the Advanced Networks module at University of Southampton

## Network architecture

A star network topology is used, with a LoPy acting as the basestation. The nodes are Raspberry Pi 3Bs (equipped with the Dragino LoRa/GPS Hat) that are paired with a Nordic Thingy:52 (via Bluetooth LE) to collect geotagged, timestamped environmental sensor data. 

Only a single node has been tested/demonstrated but the network protocol has capacity for up to 7 nodes.

![Network architecture diagram](images/network_architecture_diagram.png?raw=true "Network architecture diagram")

## Equipment used

- PyCom LoPy 1.0 [product page](https://www.adafruit.com/product/3339)
- Raspberry Pi model 3B [product page](https://www.raspberrypi.org/products/raspberry-pi-3-model-b/)
- Dragino LoRa GPS Hat (Hope RF95 with SX1276 transceiver) [product page](http://www.dragino.com/products/module/item/106-lora-gps-hat.html)
- Nordic Thingy:52 [product page](https://www.nordicsemi.com/Software-and-Tools/Development-Kits/Nordic-Thingy-52)

## Setup

### Raspberry Pi Node
A Raspberry Pi 3B is used to connect to a Thingy:52 via BTLE. This setup guide assumes a fresh install of Raspbian 9 (Stretch). The [pySX1276 library](https://github.com/mayeranalytics/pySX127x) is used for LoRa communications and [bluepy](https://github.com/IanHarvey/bluepy) is used for BTLE communications.

1. Clone this repository
2. Install a number of python packages. Superuser privileges are required to run the node's Python script, so install with `sudo` to ensure the packages are available:
```
sudo apt-get install libglib2.0-dev
sudo pip install bluepy
sudo pip install gps

# pySX1276 installation instructions:
wget https://pypi.python.org/packages/source/s/spidev/spidev-3.1.tar.gz
tar xfvz  spidev-3.1.tar.gz
cd spidev-3.1
sudo python setup.py install
```
3. Edit the Raspbian configuration file to enable SPI and UART, and to move the Pi's bluetooth connection to mini UART (to enable the GPS hat to use the PL011 UART), and to assign the SPI chip select to pin 25 (a fix as per [this forum post](https://github.com/mayeranalytics/pySX127x/issues/21#issuecomment-444596565)) 

```
sudo vim /boot/config.txt

# Uncomment these lines:
dtparam=spi=on
enable_uart=1

# Add these lines:
dtoverlay=pi3-disable-bt
dtoverlay=spi0-cs,cs0_pin=25

# Reboot to take effect
sudo reboot
```
4. To start the node, run node.py in the node directory of the repository. Provide an ID for the node (value 1-7), ensuring there are no active nodes with this ID. Ensure the GPS hat is attached with the antennas before starting. Ensure the Thingy:52 setup guide has been followed and the device is on, if required.
```
sudo python node.py <id>
```

### Thingy:52 Sensor
The Thingy:52 is found and paired using its bluetooth device name. To use a Thingy:52 with the Raspberry Pi node, change the device name to 'LoRaSensor'. This can be achieved using one of the [mobile apps](https://www.nordicsemi.com/Software-and-Tools/Development-Tools/Nordic-Thingy-52-App) for the device. 

### LoPy basestation

1. Clone the repository onto the LoPy
2. Install packages... TODO 

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


JOIN_ACK:

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

| Byte | 0                | 1                | 2                | ...              |
|------|------------------|------------------|------------------|------------------|
| Item | Latitude         | Longitude        | Sensor data      | More sensor data |
