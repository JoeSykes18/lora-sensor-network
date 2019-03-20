import threading

GPS_PORT = "/dev/ttyS0"
HEADER = "$GPRMC"

class GpsInterface(threading.Thread):
  def __init__(self):
    super(GpsInterface, self).__init__()
    self.running = False
    self.current = {}
    self.port = open(GPS_PORT, 'r')

  def run(self):
    self.running = True
    while self.running:
      line = self.port.readline()
      if line[0:6] == HEADER:
	self.current = self.parseGps(line)
	#print(self.current)

  def stop(self):
    self.running = False

  def parseGps(self, line):
    items = line.split(',')
    if items[2] == 'V':
      #print('No GPS data available')
      return None
    #print('GPS data found, parsing...')
    time = items[1][0:2] + ":" + items[1][2:4] + ":" + items[1][4:6]
    lat = self.decodeMinutes(items[3])
    latDir = items[4]
    lon = self.decodeMinutes(items[5]) 	#longitute
    lonDir = items[6] 			#longitude direction E/W

    return {'time': time, 'lat': lat, 'lat_dir': latDir, 'lon': lon, 'lon_dir': lonDir}

  def decodeMinutes(self, coord):
    #Converts DDDMM.MMMMM > DD deg MM.MMMMM min
    x = coord.split(".")
    head = x[0]
    tail = x[1]
    deg = head[0:-2]
    min = head[-2:]
    return deg + " deg " + min + "." + tail + " min"

  def getCurrent(self):
    return self.current
