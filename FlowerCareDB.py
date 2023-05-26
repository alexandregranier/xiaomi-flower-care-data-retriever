import sqlite3
import os

class FlowerCareDB:
    def __init__(self, fileName = "flower_care.db") -> None:
        self.fileName = fileName
        if not os.access(fileName, os.F_OK):
            self.connect()
            self.create_table()
        else:
            self.connect()
        pass

    def connect(self):
        self.con = sqlite3.connect(self.fileName)

    def create_table(self):

        cursor = self.con.cursor()
        cursor.execute("""CREATE TABLE data (
            device TEXT, 
            timestamp TEXT, 
            temperature REAL, 
            moisture INTEGER, 
            light INTEGER, 
            conductivity INTEGER, 
            PRIMARY KEY(device, timestamp)
        )""")

    def insert(self, historical_entry):
        
        try:
            with self.con:
                cursor = self.con.cursor()
                values = vars(historical_entry)
                sql = "INSERT INTO data VALUES(:device, :timestamp, :temperature, :moisture, :light, :conductivity)"
                cursor.execute(sql, values)
        except (sqlite3.IntegrityError):
            print ('Valeur déjà présente dans la base')
        except:
            raise sqlite3.DatabaseError
