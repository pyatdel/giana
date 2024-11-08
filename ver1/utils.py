import re
import os
from constants import VALID_GENRES

def validate_name(name):
    patterns = [
        (r'^\[(.+?)\]-\[([RV]J\d+)\] (.+?) \(([A-Z]+)\)_DLsite.*$', 'DLsite'),
        (r'^\[(.+?)\]-\[(v\d+)\] (.+?) \(([A-Z]+)\)_VNdb.*$', 'VNdb'),
        (r'^\[(.+?)\]-\[(\d+)\] (.+?) \(([A-Z]+)\)_Getchu.*$', 'Getchu'),
        (r'^\[(.+?)\]-\[(.+?)\] (.+?) \(([A-Z]+)\)_Fanza.*$', 'Fanza'),
        (r'^\[(.+?)\]-\[(.+?)\] (.+?) \(([A-Z]+)\)_Steam.*$', 'Steam')
    ]

    for pattern, platform in patterns:
        match = re.match(pattern, name)
        if match:
            creator, unique_id, game_title, genre = match.groups()

            if genre not in VALID_GENRES:
                return False, None

            if platform == 'DLsite' and not unique_id.startswith(('RJ', 'VJ')):
                return False, None

            if platform == 'VNdb' and not unique_id.startswith('v'):
                return False, None

            if platform == 'Getchu' and not unique_id.isdigit():
                return False, None

            return True, {
                "creator": creator,
                "unique_id": unique_id,
                "game_title": game_title,
                "genre": genre,
                "platform": platform
            }

    return False, None

def classify_items(items):
    valid_items = []
    invalid_items = []
    unique_ids = {}
    
    for item in items:
        is_valid, item_info = validate_name(item)
        if is_valid:
            unique_id = item_info['unique_id']
            if unique_id in unique_ids:
                unique_ids[unique_id].append(item)
            else:
                unique_ids[unique_id] = [item]
            valid_items.append((item, item_info))
        else:
            invalid_items.append(item)
    
    duplicate_items = [item for items in unique_ids.values() if len(items) > 1 for item in items]
    
    return valid_items, invalid_items, duplicate_items

def get_items_in_path(path, extensions):
    items = []
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)):
            if os.path.splitext(item)[1].lower() in extensions or '' in extensions:
                items.append(item)
        elif os.path.isdir(os.path.join(path, item)) and '' in extensions:
            items.append(item)
    return items