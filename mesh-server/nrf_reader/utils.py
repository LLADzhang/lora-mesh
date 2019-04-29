import json
import paho.mqtt.client as mqtt
import requests
import http.client
from threading import Timer

# Server Connection Parameters
SERVER = '128.46.73.96:5001'
# TIMEOUT in seconds
TIMEOUT = 10

def start_daemon(seconds, func, arguments):
    thread = Timer(seconds, func, arguments)
    #thread.daemon = True
    thread.start()
    
def battery_level_in_percent(mvolts):

    if (mvolts >= 3000):
        battery_level = 100
    elif (mvolts > 2900):
        battery_level = 100 - ((3000 - mvolts) * 58) / 100
    elif (mvolts > 2740):
        battery_level = 42 - ((2900 - mvolts) * 24) / 160
    elif (mvolts > 2440):
        battery_level = 18 - ((2740 - mvolts) * 12) / 300
    elif (mvolts > 2100):
        battery_level = 6 - ((2440 - mvolts) * 6) / 340
    else:
        battery_level = 0

    return battery_level

def send_to_server(data):
    """
    Send the data (readings) to the Web Server

    :param data: list of dictionary (keys: name, temp, nitrate) 
    """
    js_data = json.dumps(data)
    #logger.debug(js_data)
    connection = http.client.HTTPConnection(SERVER, timeout=TIMEOUT)

    headers = {'Content-type': 'application/json'}
    connection.request('POST', '/', js_data, headers)

    response = connection.getresponse()
    print(json.loads(response.read().decode())['reply'])
    connection.close()

def get_nitrate(val):
    if val and 0x00800000:
      val = ~val + 1;
      val = (val & 0x00FFFFFF)
      val = -1 * (2.4/16777216)*val
    else:
      val = (2.4/16777216) * val

    return val

def get_temp(high, low):
#    print("high 8 bits: " + "{0:b}".format(high))
 #   print("low 8 bits: " + "{0:b}".format(low))
 #   print("high 8 bits after shift by 8: " + "{0:b}".format(high << 8))
    return sign_extend((high << 8) | low) / 100
'''
  
  if val and 0x00008000:
    val = ~val + 1;
    val = (val & 0x0000FFFF)
    val = -1 * (2.4/65536)*val
  else:
    val = (2.4/65536) * val
  
  return val
'''

def sign_extend(val):
  # val is unsigned int now
    #print("converting " + "{0:b}".format(val)) 
    if val > 65535:
      raise Exception(str(val) + " is > 255")
    else:
      bits = 16
      sign_bit = 1 << (bits - 1)
      return (val & (sign_bit - 1)) - (val & sign_bit)

def mqtt_send(data):
    broker_address="localhost"
    print("creating new instance")
    client = mqtt.Client("P1") #create new instance
    client.connect(broker_address) #connect to broker
    print("connecting to broker")
    client.subscribe("mesh_gateway/data")
    print("Subscribing to topic","mesh_gateway/data")
    client.publish("mesh_gateway/data", json.dumps(data))
    print('publish succeeds') 
    client.disconnect()
    print("disconnect from mqtt server"
