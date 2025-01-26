import configparser
import os
from datetime import datetime
from pathlib import Path

INI_PATH = os.path.join(Path.home(), '.deployflow.ini')

config = configparser.ConfigParser()
config.read(INI_PATH)

def save():
    if 'misc' not in config:
        config['misc'] = {}
    config['misc']['last_saved'] = str(datetime.now())
    with open(INI_PATH, 'w') as f:
        config.write(f)

def get_val(section, key, default=None):
    return config.get(section, key, fallback=default)

def set_val(section, key, value):
    if section not in config:
        config[section] = {}
    config[section][key] = value
    save()

