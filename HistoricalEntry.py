from datetime import datetime

# Indianness
_BYTE_ORDER = 'little'

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
    def __init__(self, byte_array, epoch_time, device_address):
        epoch_offset = int.from_bytes(byte_array[:4], _BYTE_ORDER)
        #print ('timestamp = ' + str(epoch_time) + ' + ' + str(epoch_offset))
        self.timestamp = datetime.fromtimestamp(epoch_time + epoch_offset)
        # Arrondi la date a l'heure pres
        self.timestamp = self.timestamp.replace(minute=0, second=0, microsecond=0) # compensate for wall time
        self.temperature = int.from_bytes(byte_array[4:6], _BYTE_ORDER) / 10.0
        self.light = int.from_bytes(byte_array[7:10], _BYTE_ORDER)
        self.moisture = byte_array[11]
        self.conductivity = int.from_bytes(byte_array[12:14], _BYTE_ORDER)
        self.device = device_address
        #print (device_address + ' ' + self.timestamp.strftime("%m/%d/%Y, %H:%M:%S") + ' ' + str(self.temperature) + ' ')

    def __init__(self, timestamp, temperature, light, moisture, conductivity, device) :
        self.timestamp = timestamp
        self.temperature = temperature
        self.light = light
        self.moisture = moisture
        self.conductivity = conductivity
        self.device = device