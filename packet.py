from bitstring import Bits

''' Enum for the types of message that are produced
'''
class MessageType():
  JOIN = 0
  SENSOR_RESPONSE = 1
  SENSOR_REQUEST = 2


class Packet():
  ''' Network packet utilities
  '''
  def __init__(self, id, msg_type, payload):
    self.id = id
    self.type = msg_type
    self.payload = payload

  @staticmethod
  def createJoinPacket(id):
    # Packet = ID + Type + Payload
    pkt = str(id) + str(MessageType.JOIN) + '0'
    return bytearray(pkt, 'utf-8')

  @staticmethod
  def decode_packet(data):
    # first byte is ID
    id = data[0]
    msg_type = data[1]
    payload = data[2:]
    return Packet(id, msg_type, payload)

