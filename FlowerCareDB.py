import sqlite3
import psycopg2
from psycopg2.extras import execute_values
from psycopg2.errors import UniqueViolation, InFailedSqlTransaction, NumericValueOutOfRange
from configparser import ConfigParser
import os
import logging

class FlowerCareDB:
    def __init__(self, fileName = "flower_care.db") -> None:
        self.fileName = fileName
        if not os.access(fileName, os.F_OK):
            self.connect()
            self.create_tables()
        else:
            self.connect()
        pass

    def connect(self):
        self.con = sqlite3.connect(self.fileName)

    def create_tables(self):

        cursor = self.con.cursor()
        cursor.execute("""CREATE TABLE data (
            garden_fk INTEGER,
            device TEXT, 
            timestamp TEXT, 
            temperature REAL, 
            moisture INTEGER, 
            light INTEGER, 
            conductivity INTEGER, 
            PRIMARY KEY(device, timestamp),
            FOREIGN KEY (garden_fk) REFERENCES garden(id)
        )""")

        cursor.execute("""
            CREATE TABLE garden (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                device TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE device_state (
                device TEXT,
	            idx INTEGER,
                FOREIGN KEY (device) REFERENCES data (device)
            )
        """)

    def isDeviceExists(self, mac):
            """Teste l'existance du capteur dans la base
            de données à partir de son adresse mac."""
            with self.con:
                cursor = self.con.cursor()
                sql = "SELECT * FROM garden WHERE device='%s'" % mac
                cursor.execute(sql)
                if cursor.fetchone() == None: return False
                return True

    def getDevice(self, mac):
        with self.con:
            cursor = self.con.cursor()
            sql = "SELECT * FROM garden WHERE device='%s'" % mac
            cursor.execute(sql)
            return cursor.fetchone()

    def insert(self, historical_entry):
        
        try:
            with self.con:
                cursor = self.con.cursor()
                values = vars(historical_entry)
                sql = "INSERT INTO data VALUES(:id, :device, :timestamp, :temperature, :moisture, :light, :conductivity)"
                cursor.execute(sql, values)
                print (sql)
        except (sqlite3.IntegrityError):
            print ('Valeur déjà présente dans la base')
        except:
            raise sqlite3.DatabaseError
        
    def read_sqllite(self, dev=""):
        try:
            with self.con:
                cursor = self.con.cursor()
                sql = "SELECT * FROM DATA"
                if (dev != ""):
                    sql += " WHERE device=?"
                res = cursor.execute(sql, (dev,))
                return res.fetchall()
        except:
            print ("Erreur lors de la lecture de sqllite")

    def read_garden_sqllite(self):
        try:
            with self.con:
                cursor = self.con.cursor()
                sql = "SELECT * FROM garden"
                res = cursor.execute(sql)
                return res.fetchall()
        except:
            print ("Erreur lors de la lecture de sqllite")

    def synchronise(self):
        
        params = config()
        ps_con = psycopg2.connect(**params)
        cur = ps_con.cursor()

        gardens = self.read_garden_sqllite()
        for garden in gardens:
            try:
                sql = "INSERT INTO garden(id, name, device) VALUES (%s, %s, %s)"
                print (sql, garden)
                cur.execute(sql, garden)
            except (UniqueViolation) as e:
                print ("Donnée déjà présente dans la base.")
                ps_con.rollback()
        ps_con.commit()

        data = self.read_sqllite()
        
        cur = ps_con.cursor()

        for line in data:
            try:
                sql = "INSERT INTO data (id_garden, device, timestamp, temperature, moisture, light, conductivity) VALUES(%s, %s, %s, %s, %s, %s, %s)"
                print (sql, line)
                cur.execute(sql, line)
            except (UniqueViolation) as e:
                print ("Donnée déjà présente dans la base.")
                ps_con.rollback()
            except (InFailedSqlTransaction) as e:
                print ("Transaction échouée, donnée déjà présente dans la base")
                ps_con.rollback()
            except (NumericValueOutOfRange) as e:
                logging.log(logging.ERROR, 'Valeur hors des valeurs autorisées')

        ps_con.commit()
        

    def insertDevice(self, mac):
        print ("Enter garden name :")
        garden = input()
        
        with self.con:
            data = (garden, mac)
            cursor = self.con.cursor()
            sql = "INSERT INTO garden (name, device) VALUES (?,?)"
            cursor.execute(sql, data)
    
        
def config(filename='flower_care.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db
