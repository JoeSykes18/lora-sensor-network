''' Enum for the types of message that are produced
'''
class MessageType():
  JOIN_REQUEST = 0
  JOIN_ACK = 1
  SENSOR_RESPONSE = 2
  SENSOR_REQUEST = 3

''' Enum for the types of sensor available to the network
'''
class SensorType():
    TEMP = 0
    HUMID = 1
    AIR_QUAL = 2
    PRESS = 3

ALL_SENSORS = [SensorType.TEMP, SensorType.HUMID, SensorType.AIR_QUAL, SensorType.PRESS]

class Packet():
  ''' Network packet utilities
  '''
  def __init__(self, src_id, dest_id, msg_type, payload):
    self.src_id = src_id
    self.dest_id = dest_id
    self.type = msg_type
    self.payload = payload

  def __str__(self):
    return ('Packet: src_id=%d | dest_id=%d | msg_type=%d | payload=' % (self.src_id, self.dest_id, self.type)) + str(self.payload)

  @staticmethod
  def createJoinRequestPacket(id, available_sensors=[]):
    src_id = id
    dest_id = 0
    msg_type = MessageType.JOIN_REQUEST
    payload = Packet.encodeAvailableSensors(available_sensors)

    return Packet(src_id, dest_id, msg_type, payload)

  @staticmethod
  def createJoinResponsePacket(id):
    src_id = 0
    dest_id = id
    msg_type = MessageType.JOIN_ACK
    payload = 0
    return Packet(src_id, dest_id, msg_type, payload)

  @staticmethod
  def decode_packet(data):
    # first byte is ID
    src = data[0]
    dest = data[1]
    msg_type = data[2]
    payload = data[3:]

    return Packet(src, dest, msg_type, payload)

  @staticmethod
  def create_sensor_request(id, sensor_type):
    src_id = 0
    dest_id = id
    msg_type = typeMessageType.SENSOR_REQUEST
    payload = sensor_type
    return Packet(src_id, dest_id, msg_type, payload)

  @staticmethod
  def bigIntToDigits(n):
    if n < 256:
        return n
    n_str = str(n)
    return [int(i) for i in n_str] 

  @staticmethod
  def getFixedLengthInt(val, length):
    val_str = str(val)
    while len(val_str) < length:
        val_str = ['0'] + list(val_str)
    return [int(c) for c in val_str]

  @staticmethod
  def encodeGps(val):
    deg = val[0]
    mins = val[1]
    sec_str = str(val[2])
    if val[2] == 0:
        sec1 = sec2 = 0
    else:
        sec1 = int(sec_str[0:2])
        sec2 = int(sec_str[2:4])
    return [deg, mins, sec1, sec2]

  @staticmethod
  def createSensorResponse(id, sensor_type, data):
    print('Data: ', data)
    src_id = id
    dest_id = 0
    msg_type = MessageType.SENSOR_RESPONSE
    payload = [sensor_type]    
    fixedLenGps = Packet.encodeGps(data[1:4]) + Packet.encodeGps(data[4:7])
    payload.extend(fixedLenGps)
    if sensor_type is SensorType.PRESS:
        payload.extend(Packet.getFixedLengthInt(data[7], 4))
    elif sensor_type is SensorType.AIR_QUAL:
        val = Packet.getFixedLengthInt(data[7], 3)
        val.extend(Packet.getFixedLengthInt(data[8], 3))
        payload.extend(val)
    else:
        payload.extend(data[7:])

    print('Temp payload:', payload)

    return Packet(src_id, dest_id, msg_type, payload)
 
  @staticmethod
  def encode_packet(packet):
    return list(bytearray([packet.src_id, packet.dest_id, packet.type]) + bytearray(packet.payload))

  @staticmethod
  def encodeAvailableSensors(sensors):
    output = [0, 0, 0, 0]
    if SensorType.TEMP in sensors:
      output[0] = 1
    if SensorType.HUMID in sensors:
      output[1] = 1
    if SensorType.AIR_QUAL in sensors:
      output[2] = 1
    if SensorType.PRESS in sensors:
      output[3] = 1
    return output
