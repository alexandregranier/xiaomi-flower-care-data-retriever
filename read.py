from gattlib import GATTRequester
from gattlib import DiscoveryService

from struct import *

from time import time
from datetime import datetime

# service = DiscoveryService("hci0")
# devices = service.discover(2)

# for address, name in devices.item():
#     print("name {}, address: {}" . format(name,address))

# quit()

# Code service to retrieve device name i.e Flower care
DEVICE_NAME = 0x03

FIRMWARE_BATTERY_LEVEL = 0x38

DEVICE_TIME = 0x41

MODE_CHANGE_HANDLE = 0x0033

ACTUAL_SENSOR_VALUE_HANDLE = 0x35

HISTORY_CONTROL_HANDLE = 0x3e

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


class HistoricalEntry(object):
    '''
    Represents a historical entry of sensor values by parsing the byte array returned by the device.
    
    The sensor returns 16 bytes in total.
    It's unclear what the meaning of these bytes is beyond what is decoded in this method.
    
    Semantics of the data (in little endian encoding):
    bytes   0-3: timestamp, seconds since boot
    bytes   4-5: temperature in 0.1 °C
    byte      6: unknown
    bytes   7-9: brightness in lux
    byte     10: unknown
    byte     11: moisture in %
    bytes 12-13: conductivity in µS/cm
    bytes 14-15: unknown
    '''
    def __init__(self, byte_array, epoch_time):
        print (byte_array)
        epoch_offset = int.from_bytes(byte_array[:4], _BYTE_ORDER)
        self.timestamp = datetime.fromtimestamp(epoch_time + epoch_offset)
        self.timestamp = self.timestamp.replace(minute=0, second=0, microsecond=0) # compensate for wall time
        self.temperature = int.from_bytes(byte_array[4:6], _BYTE_ORDER) / 10.0
        self.light = int.from_bytes(byte_array[7:10], _BYTE_ORDER)
        self.moisture = byte_array[11]
        self.conductivity = int.from_bytes(byte_array[12:14], _BYTE_ORDER)

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

    moisture = actual_values[7]

    conductivity = int.from_bytes(value[8:10], _BYTE_ORDER)
    return [temperature, brightness, moisture, conductivity]

def _calculate_historical_entry_address(addr):
        '''Calculate address of provided historical entry index'''
        return b'\xa1' + addr.to_bytes(2, _BYTE_ORDER)

def epoch_time(gattRequester):
        '''Return the device epoch (boot) time'''
        start = time()
        response = gattRequester.read_by_handle(_HANDLE_DEVICE_TIME)[0]
        
        wall_time = (time() + start) / 2
        epoch_offset = int.from_bytes(response, _BYTE_ORDER)
        epoch_time = wall_time - epoch_offset        

        return epoch_time

req = GATTRequester("5C:85:7E:B0:0D:0B")
name = req.read_by_handle(DEVICE_NAME)[0]
print(name.decode())

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

req.write_by_handle(HISTORY_CONTROL_HANDLE, _CMD_HISTORY_READ_INIT)
entry_count = req.read_by_handle(HISTORY_DATA_HANDLE)[0]

history_length = int.from_bytes(entry_count[:2], _BYTE_ORDER)
print ("Nombre d'entrée dans l'historique : " + str(history_length))

historical_data = []

if history_length > 0:
    epoch_time = epoch_time(req)
    for i in range(history_length):
        payload = _calculate_historical_entry_address(i)
        
        print('Reading historical entry {} of {}'. format(i, str(history_length)))
        req.write_by_handle(_HANDLE_HISTORY_CONTROL, payload)
        response = req.read_by_handle(_HANDLE_HISTORY_READ)[0]
        historical_data.append(HistoricalEntry(response, epoch_time))
    
        #print('Could only retrieve {} of {} entries from the history. The rest is not readable.'. format(i, history_length))

for entry in historical_data:
    print('Timestamp: {}'.format(entry.timestamp))
    print('Temperature: {}°C'.format(entry.temperature))
    print('Moisture: {}%'.format(entry.moisture))
    print('Light: {} lux'.format(entry.light))
    print('Conductivity: {} µS/cm\n'.format(entry.conductivity))