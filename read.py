from bluepy.btle import DefaultDelegate, ScanEntry, Scanner, BTLEDisconnectError

import time
import logging
import argparse

import csv

from FlowerCareDB import FlowerCareDB
from FlowerCareDecoder import read_history, FlowerCareTimeoutException

_DEVICE_PREFIX = '5c:85:7e:'
_DEVICE_NAMES = ['flower mate', 'flower care']

_DEVICE_NAME = lambda dev: dev.getValueText(ScanEntry.COMPLETE_LOCAL_NAME)
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


_HANDLE_DEVICE_TIME = 0x41


logging.basicConfig(filename="flower_care.log",
                    level=logging.DEBUG,
                    style="{",
                    format="{asctime} [{levelname}] {message}")
logging.getLogger().addHandler(logging.StreamHandler())



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
     """Détecte les capteurs à portée"""
     delegate = ScanDelegate(lambda device : add_device(device))
     scanner = Scanner(0).withDelegate(delegate)
     result = list(filter(_DEVICE_FILTER, scanner.scan(10)))
     return result
     
def add_device(device):
     logging.log(logging.DEBUG, 'Found device {}'.format(device.addr))
     devices.append(device)


parser = argparse.ArgumentParser(description="Synchronise les données des capteurs Xiaomi Flower Care à portée")
parser.add_argument('--sync-postgres', help="Perform Postgresql synchronisation", action="store_true")
parser.add_argument('--device', help="Retrieve specified device with Mac Adress. Do not perform scan.", required=False)
parser.add_argument('--scan', help="Only perform scanning of devices", action="store_true", required=False)
parser.add_argument('--csv-only', help="Export local database to csv file", action="store_true")
args = parser.parse_args()
print(args)

if args.sync_postgres:
    logging.info("Synchronising PostgreSQL")
    db = FlowerCareDB()
    db.synchronise()
    quit()
logging.log(logging.INFO, "Start scanning for devices")

if args.csv_only:
    db = FlowerCareDB()
    device = args.device
    if device == None:
        device = ""
    data = db.read_sqllite(device)
    with open('data.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["Device", "Date", "Temperature", "Moisture", "Light", "Conductivity"])
        for line in data:
            writer.writerow(line)
    quit()

if args.device:
     device = ScanEntry(args.device, "")
     devices.append(device)
else:
    try:
        scan()
    except BTLEDisconnectError as e:
        print (e.args[0])


for device in devices:
    db = FlowerCareDB()
    if not db.isDeviceExists(device.addr):
        print (device.addr + ' not exists.')
        db.insertDevice(device.addr)

if args.scan:
    quit()



def insert_database(data):
    db = FlowerCareDB()
    for entry in data:
        # print('Device: {}'.format(entry.device))
        # print('Timestamp: {}'.format(entry.timestamp))
        # print('Temperature: {}°C'.format(entry.temperature))
        # print('Moisture: {}%'.format(entry.moisture))
        # print('Light: {} lux'.format(entry.light))  
        # print('Conductivity: {} µS/cm\n'.format(entry.conductivity))
        entry.id = db.getDevice(entry.device)[0]
        db.insert(entry)


for device in devices:
    try:
       data = read_history(device.addr)
       insert_database(data)
    except (FlowerCareTimeoutException) as e:
        print ("Timeout reading {}".format(device.addr))
    

if args.sync_postgres:
    logging.info("Synchronising PostgreSQL")
    db = FlowerCareDB()
    db.synchronise()
logging.shutdown()