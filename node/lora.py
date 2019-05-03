#!/usr/bin/env python3

""" A simple continuous receiver class. """

# Copyright 2015 Mayer Analytics Ltd.
#
# This file is part of pySX127x.
#
# pySX127x is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pySX127x is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You can be released from the requirements of the license by obtaining a commercial license. Such a license is
# mandatory as soon as you develop commercial activities involving pySX127x without disclosing the source code of your
# own applications, or shipping pySX127x with a closed source product.
#
# You should have received a copy of the GNU General Public License along with pySX127.  If not, see
# <http://www.gnu.org/licenses/>.


import threading
from time import sleep
from SX127x.LoRa import *
from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD

BOARD.setup()

class LoRaUtil(LoRa):
    def __init__(self, verbose=False):
        super(LoRaUtil, self).__init__()
	self.init_lora(verbose)
	self.rx_buffer = []
 
    def init_lora(self, verbose):
        parser = LoRaArgumentParser("LoRa util")
	args = parser.parse_args(self)
	print(self)
	self.set_mode(MODE.STDBY)
	self.set_pa_config(pa_select=1)
	assert(self.get_agc_auto_on() == 1)
	self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)
 
    def on_rx_done(self):
        BOARD.led_on()
        print("\nRxDone")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        self.rx_buffer.append(payload.decode())
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        BOARD.led_off()
        self.set_mode(MODE.RXCONT)

    def on_tx_done(self):
        print("\n[LoRa] Transmission successful")
        print(self.get_irq_flags())

    def on_cad_done(self):
        print("\non_CadDone")
        print(self.get_irq_flags())

    def on_rx_timeout(self):
        print("\non_RxTimeout")
        print(self.get_irq_flags())

    def on_valid_header(self):
        print("\non_ValidHeader")
        print(self.get_irq_flags())

    def on_payload_crc_error(self):
        print("\non_PayloadCrcError")
        print(self.get_irq_flags())

    def on_fhss_change_channel(self):
        print("\non_FhssChangeChannel")
        print(self.get_irq_flags())

    def send(self, pkt):
	self.write_payload(pkt)
	self.set_mode(MODE.TX)
	print('[LoRa] Payload written')

    def recv(self):
	while(len(self.rx_buffer) == 0):
	  sleep(0.1)
	item = self.rx_buffer[0]
	self.rx_buffer = self.rx_buffer[1:]
	return item
  
    def start(self):
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        
	try: 
	  while 1:
	      sleep(.1)
	except KeyboardInterrupt:
	  print('[LoRa] Keyboard interrupt')
	finally:
	  self.set_mode(MODE.SLEEP)
	  BOARD.teardown()
