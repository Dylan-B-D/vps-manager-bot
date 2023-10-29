# util/data_utils.py

# Standard Libraries
import os
from datetime import datetime
import configparser

# Third-party Libraries
import bson


def save_login_state(key, value, filepath):
    """Save the login state to a BSON cache file."""
    current_time = datetime.utcnow()
    login_states = load_from_bson(filepath)

    # Convert the tuple to a string key
    string_key = f"{key[0]}_{key[1]}"

    login_states[string_key] = {"vps_name": value, "timestamp": current_time}
    save_to_bson(login_states, filepath)


def get_login_state(server_id, channel_id, filepath):
    """Retrieve the login state for a given server and channel from the cached BSON file."""
    login_states = load_from_bson(filepath)
    string_key = f"{server_id}_{channel_id}"
    return login_states.get(string_key, {}).get("vps_name", None)



def save_to_bson(data, filepath):
    """Save the data to a BSON file."""
    with open(filepath, 'wb') as f:
        f.write(bson.BSON.encode(data))

def load_from_bson(filepath):
    """Load data from a BSON file. If the file doesn't exist or is empty, return an empty dictionary."""
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return {}
    with open(filepath, 'rb') as f:
        return bson.BSON(f.read()).decode()
    

def load_vps_configs(config):
    """
    Load VPS configurations from a given config parser object.
    """
    vpses = {}
    for section in config.sections():
        if section != "Bot":  # Exclude the Bot section
            vpses[section] = {
                'IP': config[section]['IP'],
                'Username': config[section]['Username'],
                'Password': config[section]['Password']
            }
    return vpses

def setup_cache_directory(base_filename=__file__):
    """
    Set up the cache directory and return its path.
    """
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(base_filename), '..'))
    CACHE_DIR = os.path.join(BASE_DIR, 'data', 'cache')

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    return CACHE_DIR

def get_bot_token(config_file='config.ini'):
    """
    Retrieve the bot token from a configuration file.
    """
    config = configparser.ConfigParser()
    
    try:
        config.read(config_file)
        return config['Bot']['Token']
    except (configparser.Error, KeyError) as e:
        raise SystemExit("Error reading configuration file.") from e