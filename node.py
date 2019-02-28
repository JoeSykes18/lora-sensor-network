from bluepy import btle

print("Scanning for BTLE devices")
 
scanner = btle.Scanner()
devices = scanner.scan(20)

for dev in devices:
	print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi)) 

print("Connecting to Thingy...")
dev = btle.Peripheral("DE:AA:A8:87:82:CA", addrType=btle.ADDR_TYPE_RANDOM)
 
print("Connected. Services...")
for svc in dev.services:
    print str(svc)
