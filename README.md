# Xiaomi data retreiver

## Installation

### Dépendances

```
sudo apt install libglib2.0-dev libpq-dev libboost-python-dev libbluetooth-dev libboost-thread-dev

pip install bluepy psycopg2 gattlib
```
### Permettre l'exécution sans les droits administrateurs

```
find /usr/local/lib -name bluepy-helper # ou find . -name bluepy-helper
/usr/local/lib/python3.10/dist-packages/bluepy-1.3.0-py3.10.egg/bluepy/bluepy-helper
sudo setcap 'cap_net_raw,cap_net_admin+eip' /usr/local/lib/python3.10/dist-packages/bluepy-1.3.0-py3.10.egg/bluepy/bluepy-helper
```