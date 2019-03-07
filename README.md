# LoRa Sensor Network
A wireless sensor network using LoRa for the Advanced Networks module at University of Southampton

## Setup
### Raspberry Pi Node
A Raspberry Pi Zero W was used to connect to a Nordic Thingy 52 forming the nodes on the network. The Pi Zero is equipped with Bluetooth LE meaning it is capable of communicating with the Thingy.

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
