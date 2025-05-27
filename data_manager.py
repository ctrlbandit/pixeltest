
import json
import os

# File paths
PROFILES_FILE = "global_profiles.json"
CATEGORY_BLACKLIST_FILE = "category_blacklist.json"
BLACKLIST_FILE = "channel_blacklist.json"

# Global profiles management
def load_global_profiles():
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_profiles(profiles):
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=4)

# Category blacklist management
def load_category_blacklist():
    if not os.path.exists(CATEGORY_BLACKLIST_FILE):
        with open(CATEGORY_BLACKLIST_FILE, "w") as f:
            json.dump({}, f)
    
    with open(CATEGORY_BLACKLIST_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_category_blacklist(blacklist):
    with open(CATEGORY_BLACKLIST_FILE, "w") as f:
        json.dump(blacklist, f, indent=4)

# Channel blacklist management
def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        with open(BLACKLIST_FILE, "w") as f:
            json.dump({}, f)
    
    with open(BLACKLIST_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(blacklist, f, indent=4)

# Initialize data
global_profiles = load_global_profiles()
category_blacklist = load_category_blacklist()
channel_blacklist = load_blacklist()
