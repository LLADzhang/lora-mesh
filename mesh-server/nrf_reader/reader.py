"""
Readings Collector
"""
import serial
import re
import requests
import http.client
import json
import time
import traceback
import sys
import math
import logging
import datetime
from enum import Enum
from prettytable import PrettyTable
from utils import battery_level_in_percent, send_to_server, get_nitrate, get_temp, sign_extend, mqtt_send, mqtt_connect, mqtt_disconnect

__version__ = '2.0'
__author__ = "heng"

class Msg_Type(Enum):
  MESH_TYPE_UNKNOWN = 0
  MESH_TYPE_DATA = 1
  MESH_TYPE_ACK = 2
  MESH_TYPE_FORWARD = 3
  MESH_TYPE_HELLO = 4
  MESH_TYPE_ROUTE_DISCOVERY_REQUEST = 5
  MESH_TYPE_ROUTE_DISCOVERY_RESPONSE = 6
  MESH_TYPE_ROUTE_FAILURE = 7
  MESH_TYPE_NULL = 8
  MESH_TYPE_RT_REPORT = 9
  MESH_TYPE_RT_GATHER = 10
  MESH_TYPE_RT_FORWARD = 11
  MESH_TYPE_SCHEDULE = 12

# Serial Connection Parameters
DEFAULT_PORT = '/dev/tty.usbmodem1411'           # Connection Port
SPEED = 115200                  # Baud Rate

HEADER_SIZE = 10                # the first 10 bytes are header
MAX_NODE = 40
BATCH  = 0                      # Batch limit used for uploading readings

PATTERN_HEAD = '<info> app: source: {(.*)}, destination: {(.*)}, prev: {(.*)}, dataType: {(.*)}, msg_id: {(.*)}'
PATTERN_DATA = '<info> app: nitrate: {(.*)}, temperature: {(.*)}, humidity: {(.*)}, battery: {(.*)} {(.*)}'
PATTERN_GENERAL = '<info> app: {(.*)}'

# logging
# create logger
filename = 'logs/collect-readings-' + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.log' 
logging.basicConfig(filename=filename, filemode='w', level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('collect-logger')

TEST_RT = {1: [{'neighbor': False, 'rssi': 255}, {'neighbor': True, 'rssi': -32}, {'neighbor': False, 'rssi': 255}, {'neighbor': False, 'rssi': 255}]}

def connect(port):
    """
        Establish a connection to the serial port and start to collect readings
        from the serial port
    """
    mqtt_cli = mqtt_connect()
    list = []
    reading = {}
    readings = []

    #print("Collecting readings from " + port)
    logger.info('Collection readings from ' + port)

    input = serial.Serial(
        port=port, 
        baudrate=SPEED,
        timeout=0.5
        )
   
    while input.isOpen():
      try:
        data_lines = input.readlines()
        if not data_lines:
            print([])
        else:
          
          for line in data_lines:
            data = line.decode('utf-8').split()
           # print(data)
            rssi = int(data[0])
            #print('rssi:', rssi)
            hexarray = []
            for x in data[1:]:
      
              if len(x) == 2:
                hexarray.append('0x'+x)
              elif len(x) == 1:
                hexarray.append("0x0" + x)
              else:
                raise Exception(x, "lenght is not 1 or 2")
            #print(hexarray, len(hexarray))
            data = [int(x, 16) for x in hexarray]
            #print(len(data), " bytes")
            #print(data)
            try:
              msg_type = Msg_Type(data[4])
            except:
              traceback.print_exc()
              msg_type = Msg_Type.MESH_TYPE_UNKNOWN
              
            if msg_type == Msg_Type.MESH_TYPE_RT_REPORT:

             # logger.info(str(time.ctime(int(time.time())))
              #            + " # of Entries = " + str(data[1])
              #             + "\n"
              #            )
              table = PrettyTable()

              #table.field_names = ["isNeighbor", "# of Hops", "Next Hop", "State", "Remaining Timeout", "RSSI"]
              table.field_names = ["isNeighbor", "# of Hops", "Next Hop", "State", "RSSI"]
              length = 5
              owner = data[0]
              rt = {owner:[]}
              for i in range(1, int(data[1]) + 1):
                state = ['Invalid', 'Valid'][int(data[9 + (i - 1) * length + 3])]
                rssi = sign_extend((data[9 + (i - 1) * length + 4] << 8 | data[9 + (i - 1) * length + 5]))
                table.add_row([data[9 + (i - 1) * length + 1], data[9 + (i - 1) * length + 2], i,
                               state, rssi])
                if state == 'Valid' and data[9 + (i - 1) * length + 1] == 1:
                    rt[owner].append({'n': i, 'r':rssi})
                else:
                  rt[owner].append({'n': 255, 'rssi':0})
              #print("RT report from node", data[0])
              #print(table)
#              print(rt)
              mqtt_send(mqtt_cli, rt)
      except KeyboardInterrupt:
          exit()
      except:
        traceback.print_exc()
        
    input.close()

def main():
    """
        Main routine
    """

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    port = DEFAULT_PORT;

    if ( len (sys.argv) > 1 ):
        port = sys.argv[1];

    connect(port)


if __name__ == "__main__":
    main()
