from gattlib import GATTRequester, GATTException, BTIOException
import time
from HistoricalEntry import HistoricalEntry

_BYTE_ORDER = 'little'

_HANDLE_DEVICE_TIME = 0x41
_HANDLE_HISTORY_CONTROL = 0x3e
_HANDLE_HISTORY_READ = 0x3c
_CMD_HISTORY_READ_INIT = bytes([0xa0, 0x00, 0x00])
HISTORY_DATA_HANDLE = 0x3c

class FlowerCareDecoder:

    def __init__(self, mac_address) -> None:
        self.mac_address = mac_address
        # Flag to check connexion status
        self.connected = False
        self.e_time = 0
        self.history_count = 0
        self.history_counter = 0
        self.payload = ""
        
    def ManageConnection(fn):
        def wrapper(self):
            completed = False
            self.gattRequester = self.connect()
            while not completed:
                try:
                    return fn(self)
                except (BTIOException) as e:
                    print("Déconnexion lors de la récupération de l'heure de démarrage du capteur ... Nouvel essai")
                    self.connected = False
                    time.sleep(1)
                except (GATTException) as ge:
                    print("Perte de signal lors de la récupération de l'heure de démarrage du capteur ... Nouvel essai")
                    self.connected = False
                    time.sleep(1)
        return wrapper

    @ManageConnection
    def epoch_time(self):
        '''Return the device epoch (boot) time in seconds since 1/01/70'''
        self.gattRequester = self.connect()
        
        response = self.gattRequester.read_by_handle(_HANDLE_DEVICE_TIME)[0]
        start = time.time()
        wall_time = (time.time() + start) / 2
        epoch_offset = int.from_bytes(response, _BYTE_ORDER)
        self.e_time = wall_time - epoch_offset        

        return self.e_time

    @ManageConnection
    def get_history_count(self):
        self.gattRequester.write_by_handle(_HANDLE_HISTORY_CONTROL, _CMD_HISTORY_READ_INIT)
        entry_count = self.gattRequester.read_by_handle(HISTORY_DATA_HANDLE)[0]
        self.history_count = int.from_bytes(entry_count[:2], _BYTE_ORDER)
        return self.history_count

    
    def read_history(self):
        historical_data = []
        for self.history_counter in range(self.history_count):
            self.payload = b'\xa1' + self.history_counter.to_bytes(2, _BYTE_ORDER)
            print('Reading historical entry {} of {}'. format(self.history_counter, str(self.history_count)))
            response = self.read_history_entry()
            historical_data.append(HistoricalEntry(response, self.e_time, self.mac_address))
        return historical_data

    @ManageConnection
    def read_history_entry(self):
        self.gattRequester.write_by_handle(_HANDLE_HISTORY_CONTROL, self.payload)
        response = self.gattRequester.read_by_handle(_HANDLE_HISTORY_READ)[0]
        return response

    def connect(self):
        if not self.connected:
            req = GATTRequester(self.mac_address)
            print ("Connexion...")
            self.connected = True
            return req
        else:
            return self.gattRequester
        
    @staticmethod
    def parseHistoryEntry(entry):
        return {}
    
    