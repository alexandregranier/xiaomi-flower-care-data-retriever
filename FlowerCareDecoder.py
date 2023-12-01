from gattlib import GATTRequester, GATTException, BTIOException
import time, sys
from datetime import datetime
from HistoricalEntry import HistoricalEntry
from struct import unpack

_BYTE_ORDER = 'little'

_HANDLE_DEVICE_TIME = 0x41
_HANDLE_HISTORY_CONTROL = 0x3e
_HANDLE_HISTORY_READ = 0x3c
_CMD_HISTORY_READ_INIT = bytes([0xa0, 0x00, 0x00])
HISTORY_DATA_HANDLE = 0x3c
DEVICE_NAME = 0x03
MODE_CHANGE_HANDLE = 0x0033
_CMD_BLINK_LED = bytes([0xfd, 0xff])
FIRMWARE_BATTERY_LEVEL = 0x38
_CMD_REAL_TIME_READ_INIT = bytes([0xa0, 0x1f])
ACTUAL_SENSOR_VALUE_HANDLE = 0x35

# Après 10 mn on stope les essais
TIMEOUT =  1200


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

    temperature, brightness, moisture, conductivity = parseData(actual_values)

    print ("Température : " + str(temperature) + " °C")
    print ("Luminosité : " + str(brightness) + " lux")
    print ("Humidité : " + str(moisture) + " %")
    print ("Conductivité " + str(conductivity) + " µS/cm")
    return req

def read_history(dev):
    e_time = get_epoch_time(dev)
    return get_history_info(dev, e_time)


def get_epoch_time(dev):
    e_time = 0
    try:
        print ('Lecture de ', dev)
        req = GATTRequester(dev)
        connected = True
        e_time_ok = False
        while not e_time_ok:
            start_time = time.time()
            timeout = (True if time.time() > start_time + TIMEOUT else False)
            if timeout:
                raise FlowerCareTimeoutException()
            try:
                if not connected:
                    req = GATTRequester(dev)
                    connected = True
                response = req.read_by_handle(_HANDLE_DEVICE_TIME)[0]
                start = time.time()
                wall_time = (time.time() + start) / 2
                epoch_offset = int.from_bytes(response, _BYTE_ORDER)
                e_time = wall_time - epoch_offset
                print ('epoch_time {}', datetime.fromtimestamp(e_time))
                e_time_ok = True
                req.disconnect()
            except (BTIOException) as e:
                print("déconnecté durant récupération device_time")
                connected = False
                time.sleep(1)
            except (GATTException) as ge:
                print("répond plus durant récupération device_time!")
                connected = False
                time.sleep(1)
    except (GATTException, BTIOException) as ge:
        print("Exception ailleurs")
    return e_time


def get_history_info(dev, e_time):
    history_info_ok = False
    history_length = 0
    start_time = time.time()
    historical_data = []
    counter = 1

    while not history_info_ok:
        timeout = (True if time.time() > start_time + TIMEOUT else False)
        if timeout:
            raise FlowerCareTimeoutException()
        try:
            req = GATTRequester(dev)
            print ("Write history handle in ", dev)
            req.write_by_handle(_HANDLE_HISTORY_CONTROL, _CMD_HISTORY_READ_INIT)
            print ("Read history data handle")
            entry_count = req.read_by_handle(HISTORY_DATA_HANDLE)[0]

            history_length = int.from_bytes(entry_count[:2], _BYTE_ORDER)
            print ("History length : {}" .format(history_length))
            history_info_ok = True
            req.disconnect()
            if history_length > 0:
                for i in range(counter, history_length, 1):
                    payload = calculate_historical_entry_address(i)
                    retreived = False
                    while not retreived:
                        try:
                            req = GATTRequester(dev)
                            print('Reading historical entry {} of {} payload {}'. format(i, str(history_length), payload))
                            req.write_by_handle(_HANDLE_HISTORY_CONTROL, payload)
                            response = req.read_by_handle(_HANDLE_HISTORY_READ)[0]
                            historical_data.append(HistoricalEntry(response, e_time, dev))
                            print ("size : {}", sys.getsizeof(historical_data))
                            retreived = True
                            req.disconnect()
                            counter+= 1
                            start_time = time.time()
                        except (BTIOException) as e:
                            print("déconnecté")
                            connected = False
                            time.sleep(1)
                        except (GATTException) as ge:
                            print("répond plus !")
                            connected = False
                            time.sleep(1)
                            history_info_ok = False
                            raise Exception("Déconnexion durant lecture historique")
        except (BTIOException) as e:
            print("déconnecté durant récupération info historique")
            connected = False
            time.sleep(1)
        except (GATTException) as ge:
            print("répond plus durant récupération info historique!")
            connected = False
            time.sleep(1)
        except (Exception) as e:
            history_info_ok = False
            print (e)

    return historical_data

    
    
    
        #print('Could only retrieve {} of {} entries from the history. The rest is not readable.'. format(i, history_length))
    return historical_data

        
        

def calculate_historical_entry_address(addr):
    '''Calculate address of provided historical entry index'''
    return b'\xa1' + addr.to_bytes(2, _BYTE_ORDER)

class FlowerCareTimeoutException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    
    def __str__(self) -> str:
        return "Timeout exception after {}mn ".format(TIMEOUT)