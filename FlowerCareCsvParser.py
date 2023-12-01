import csv, re
from HistoricalEntry import HistoricalEntry
# Un fichier csv peut contenir les données de plusieurs capteurs
# 
# Ils sont identifiés par leur adresse MAC au format IEEE 802
# trouvable sur la première colonne (3e ligne pour le premier capteur) 
# selon le format : Flower Care (5C:85:7E:B0:02:95)

SENSOR_MAC_REGEX = "^Flower Care \\((([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}))\\)$"

# Suivi de l'espèce surveillée (qui ne nous intéresse pas) et la date sur la 2e colonne
# La date est répété toutes les 4 colonnes
DATE_REGEX = "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
# suivi de l'entête de la variable L, S, T et E (lumière, humidité, température, conductivité)

# suivi de 24 lignes contenant les données pour chaque heure
# L'heure est dans la première colonne encadré par des crochets [15:00]
TIME_REGEX = "^\\[([0-9][0-9]:[0-9][0-9])\\]$"

# en cas d'absence de donnée 2 tirets (--)

index_date = {}

# Liste pour contenir toutes les mesures du fichier
historical_data = []

# Adresse MAC du capteur
current_sensor_mac = ""

with open("2023-11-30-10-HHCC.csv", encoding='utf-16') as csvfile:
    reader = csv.reader(csvfile, delimiter="\t")
    for row in reader:
        # Test adresse MAC
        if len(row) == 0:
            continue

        result_mac = re.search(SENSOR_MAC_REGEX, row[0])
        if result_mac != None:
            if 'current_sensor_mac' in vars():
                print (index_date)
            current_sensor_mac = result_mac.group(1).strip()
            print ("Adresse MAC :", current_sensor_mac)
            
            # On re-initialise le tableau des dates
            index_date = {}
            
        # Test sur la date du jour (2e colonne et toute les 4 colonnes indice 1, 5, 10, 15 etc.)
        idx = 1
        for cell in row[1:]:    # on saute le premier élément qui contient l'espèce
            result_date = re.search(DATE_REGEX, cell)
            if result_date != None:
                index_date[idx] = cell
            idx += 1
        
        # On saute la ligne des entêtes dont la première cellule est vide
        if row[0] == None:
            continue
        # Traitement d'une ligne
        result_time = re.search(TIME_REGEX, row[0])
        idx_col = 1
        if result_time != None:
            time = result_time.group(1)
            print (f'{current_sensor_mac} {time}')
            meas_idx = 0
            for cell in row[1:]:    # On saute le premier élément qui contient l'heure
                light, soil_humidity, temperature, conductivity = 0, 0, 0, 0
                meas_idx += 1
                if idx_col > 4:
                    idx_date = ((idx_col // 4) * 4) + 1
                else:
                    idx_date = 1
                date = index_date[idx_date]
                # Dans la base la date est de la forme AAAA-MM-JJ HH:mm:ss
                timestamp = f'{date} {time}'
                if meas_idx == 1:
                    light = cell
                if meas_idx == 2:
                    soil_humidity = cell
                if meas_idx == 3:
                    temperature = cell
                if meas_idx == 4:   # On dispose de toutes les données pour créer une entrée d'historique
                    conductivity = cell
                    historical_data.append(HistoricalEntry(timestamp, temperature, light, soil_humidity, conductivity, current_sensor_mac))
                    meas_idx = 0

                # print (f'{timestamp} {cell}')
                idx_col += 1
                if idx_col >= len(index_date) * 4:
                    break

print (historical_data)


