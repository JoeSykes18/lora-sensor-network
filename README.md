# LoRa Sensor Network
A wireless sensor network using LoRa for the Advanced Networks module at University of Southampton

## Setup
### Raspberry Pi Node
A Raspberry Pi Zero W was used to connect to a Nordic Thingy 52 forming the nodes on the network. The Pi Zero is equipped with Bluetooth LE meaning it is capable of communicating with the Thingy.

The python `bluepy` library was used for communications. The following tutorials helped:
https://www.elinux.org/RPi_Bluetooth_LE
https://stackoverflow.com/questions/32947807/cannot-connect-to-ble-device-on-raspberry-pi
