from gattlib import GATTRequester, GATTException, BTIOException


from bluepy.btle import DefaultDelegate, ScanEntry, Scanner, BTLEDisconnectError

from struct import *

import time
import logging
from datetime import datetime

from concurrent import futures

from pprint import pprint

from HistoricalEntry import HistoricalEntry
from FlowerCareDB import FlowerCareDB
from FlowerCareDecoder import FlowerCareDecoder

# service = DiscoveryService("hci0")
# devices = service.discover(2)

# for address, name in devices.item():
#     print("name {}, address: {}" . format(name,address))


_DEVICE_PREFIX = '5c:85:7e:'
_DEVICE_NAMES = ['flower mate', 'flower care']

_DEVICE_NAME = lambda dev: dev.getValueText(ScanEntry.COMPLETE_LOCAL_NAME)
_DEFAULT_CALLBACK = lambda dev: print('Found new device', dev.addr, _DEVICE_NAME(dev))
_DEVICE_FILTER = lambda dev: (dev.addr and dev.addr.lower().startswith(_DEVICE_PREFIX)) \
    and (_DEVICE_NAME(dev) and _DEVICE_NAME(dev).lower() in _DEVICE_NAMES)

# Code service to retrieve device name i.e Flower care
DEVICE_NAME = 0x03

FIRMWARE_BATTERY_LEVEL = 0x38

DEVICE_TIME = 0x41

MODE_CHANGE_HANDLE = 0x0033

ACTUAL_SENSOR_VALUE_HANDLE = 0x35

HISTORY_DATA_HANDLE = 0x3c

_BYTE_ORDER = 'little'

_HANDLE_DEVICE_NAME = 0x03
_HANDLE_DEVICE_TIME = 0x41
_HANDLE_DATA_READ = 0x35
_HANDLE_MODE_CHANGE = 0x33
_HANDLE_FIRMWARE_AND_BATTERY = 0x38
_HANDLE_HISTORY_CONTROL = 0x3e
_HANDLE_HISTORY_READ = 0x3c

_CMD_BLINK_LED = bytes([0xfd, 0xff])
_CMD_REAL_TIME_READ_INIT = bytes([0xa0, 0x1f])
_CMD_HISTORY_READ_INIT = bytes([0xa0, 0x00, 0x00])
_CMD_HISTORY_READ_SUCCESS = bytes([0xa2, 0x00, 0x00])
_CMD_HISTORY_READ_FAILED = bytes([0xa3, 0x00, 0x00])

logging.basicConfig(filename="flower_care.log",
                    level=logging.DEBUG,
                    style="{",
                    format="{asctime} [{levelname}] {message}")

def parseData(value):
    """
    Analyse la chaine de données renvoyé par le capteur
        Bytes	    Type	    Value	Description
        00-01	    uint16	    234	    temperature in 0.1 °C
        02	        ?	        ?	    ?
        03-06	    uint32	    171	    brightness in lux
        07	        uint8	    21	    moisture in %
        08-09	    uint16	    178	    conductivity in µS/cm
        10-15	    ?	        ?	    ?
    """

    temperature = int.from_bytes(value[:2], _BYTE_ORDER) / 10

    brightness = int.from_bytes(value[3:7], _BYTE_ORDER)

    moisture = int.from_bytes(value[7:8], _BYTE_ORDER)

    conductivity = int.from_bytes(value[8:10], _BYTE_ORDER)
    return [temperature, brightness, moisture, conductivity]

def calculate_historical_entry_address(addr):
        '''Calculate address of provided historical entry index'''
        return b'\xa1' + addr.to_bytes(2, _BYTE_ORDER)

def epoch_time(gattRequester):
        '''Return the device epoch (boot) time'''
        start = time.time()
        response = gattRequester.read_by_handle(_HANDLE_DEVICE_TIME)[0]
        
        wall_time = (time.time() + start) / 2
        epoch_offset = int.from_bytes(response, _BYTE_ORDER)
        epoch_time = wall_time - epoch_offset        

        return epoch_time

class ScanDelegate(DefaultDelegate):
    '''
    Represents a delegate called upon the discovery of each new device
    '''

    def __init__(self, callback):
        DefaultDelegate.__init__(self)
        self.callback = callback
 
    def handleDiscovery(self, dev, is_new_device, is_new_data):
        if is_new_device and _DEVICE_FILTER(dev):
                self.callback(dev)

devices = []

def scan():
     delegate = ScanDelegate(lambda device : add_device(device))
     scanner = Scanner(0).withDelegate(delegate)
     result = list(filter(_DEVICE_FILTER, scanner.scan(10)))
     return result
     
def add_device(device):
     logging.log(logging.DEBUG, 'Found device {}'.format(device.addr))
     devices.append(device)

def read_current_data(dev, epoch_time):
    print ('Lecture de ', dev)
    req = GATTRequester(dev)
    name = req.read_by_handle(DEVICE_NAME)[0]
    print(name.decode())
    req.write_by_handle(MODE_CHANGE_HANDLE, _CMD_BLINK_LED) 

    firm_ware_data = req.read_by_handle(FIRMWARE_BATTERY_LEVEL)[0]
    print (firm_ware_data)
    battery, version = unpack('<B6s', firm_ware_data)

    print("Firmware version " + str(version))

    print ("Battery level " + str(battery) + " %")

    device_time = epoch_time(req)
    print ("Unix timestamp : " + str(time()))
    date_time = datetime.fromtimestamp(time())
    print ("Date & time " + date_time.strftime('%Y-%m-%d %H:%M:%S'))

    seconds_since_boot = device_time
    print ("Seconds since boot : " + str(seconds_since_boot) + " seconds")
    date_of_boot = datetime.fromtimestamp(device_time)
    print ("Date of boot : " + date_of_boot.strftime('%Y-%m-%d %H:%M:%S'))

    req.write_by_handle(MODE_CHANGE_HANDLE, _CMD_REAL_TIME_READ_INIT)
    actual_values = req.read_by_handle(ACTUAL_SENSOR_VALUE_HANDLE)[0]
# print (actual_values)
# print (str(actual_values[3:6]))
# print (str(actual_values[7]))
# print (str(actual_values[8:10]))

    temperature, brightness, moisture, conductivity = parseData(actual_values)

    print ("Température : " + str(temperature) + " °C")
    print ("Luminosité : " + str(brightness) + " lux")
    print ("Humidité : " + str(moisture) + " %")
    print ("Conductivité " + str(conductivity) + " µS/cm")
    return req

logging.log(logging.INFO, "Start scanning for devices")
result = []
try:
    result = scan()
except BTLEDisconnectError as e:
     print (e.args[0])
print ('Après scan')


def read_history(dev):
    done = False
    try:
        print ('Lecture de ', dev)
        timeout = time.time() + 10
        req = GATTRequester(dev)
        e_time_ok = False
        while not e_time_ok:
            try:
                response = req.read_by_handle(_HANDLE_DEVICE_TIME)[0]
                start = time.time()
                wall_time = (time.time() + start) / 2
                epoch_offset = int.from_bytes(response, _BYTE_ORDER)
                e_time = wall_time - epoch_offset
                print ('epoch_time {}', datetime.fromtimestamp(e_time))
                e_time_ok = True
            except (BTIOException) as e:
                print("déconnecté durant récupération device_time")
                connected = False
                time.sleep(1)
            except (GATTException) as ge:
                print("répond plus durant récupération device_time!")
                connected = False
                time.sleep(1)

        connected = False

        while not done or time.time() < timeout:
            
            
            history_info_ok = False
            history_length = 0
            while not history_info_ok:
                try:
                    req = GATTRequester(dev)
                    connected = True
                    if not connected:
                        req = GATTRequester(dev)
                        connected = True
                    req.write_by_handle(_HANDLE_HISTORY_CONTROL, _CMD_HISTORY_READ_INIT)
                    entry_count = req.read_by_handle(HISTORY_DATA_HANDLE)[0]

                    history_length = int.from_bytes(entry_count[:2], _BYTE_ORDER)
                    history_info_ok = True
                except (BTIOException) as e:
                    print("déconnecté durant récupération info historique")
                    connected = False
                    time.sleep(1)
                except (GATTException) as ge:
                    print("répond plus durant récupération info historique!")
                    connected = False
                    time.sleep(1)
            """ history_length = 10 """
            print ("Nombre d'entrée dans l'historique : " + str(history_length))

            historical_data = []
            
            if history_length > 0:
                
                for i in range(history_length):
                    
                    payload = calculate_historical_entry_address(i)
                
                    print('Reading historical entry {} of {}'. format(i, str(history_length)))
                    retreived = False
                    while not retreived:
                        try:
                            if not connected:
                                req = GATTRequester(dev)
                                connected = True
                            req.write_by_handle(_HANDLE_HISTORY_CONTROL, payload)
                            response = req.read_by_handle(_HANDLE_HISTORY_READ)[0]
                            historical_data.append(HistoricalEntry(response, e_time, dev))
                            retreived = True
                        except (BTIOException) as e:
                            print("déconnecté")
                            connected = False
                            time.sleep(1)
                        except (GATTException) as ge:
                            print("répond plus !")
                            connected = False
                            time.sleep(1)
                #print('Could only retrieve {} of {} entries from the history. The rest is not readable.'. format(i, history_length))
            else: 
                break
            return historical_data
        done = True
    except (GATTException, BTIOException) as ge:
        print("Exception ailleurs")
    
    
def insert_database(data):
    db = FlowerCareDB()
    for entry in data:
        print('Device: {}'.format(entry.device))
        print('Timestamp: {}'.format(entry.timestamp))
        print('Temperature: {}°C'.format(entry.temperature))
        print('Moisture: {}%'.format(entry.moisture))
        print('Light: {} lux'.format(entry.light))  
        print('Conductivity: {} µS/cm\n'.format(entry.conductivity))
        db.insert(entry)
#e = futures.ThreadPoolExecutor(max_workers = 5)



for device in devices:
     #e.submit(read_history, device.addr, epoch_time)
     data = read_history(device.addr)
     insert_database(data)

#e.shutdown()
logging.shutdown()