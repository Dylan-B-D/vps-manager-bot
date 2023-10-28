# Standard Libraries
import os
from datetime import datetime

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