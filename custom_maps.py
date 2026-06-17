import json
import os

CUSTOM_MAPS_FILE = os.path.join(os.path.dirname(__file__), "custom_maps.json")

def load_custom_maps():
    try:
        if os.path.exists(CUSTOM_MAPS_FILE):
            with open(CUSTOM_MAPS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading custom maps: {e}")
    return []

def save_custom_maps(maps):
    try:
        with open(CUSTOM_MAPS_FILE, "w", encoding="utf-8") as f:
            json.dump(maps, f, indent=2)
            return True
    except Exception as e:
        print(f"Error saving custom maps: {e}")
    return False

def add_custom_map_with_name(name, grid, rows, cols):
    maps = load_custom_maps()
    # Check if a map with the same name exists to overwrite
    existing_map = None
    cleaned_name = name.strip().upper()
    for m in maps:
        if m["name"].strip().upper() == cleaned_name:
            existing_map = m
            break
            
    if existing_map:
        existing_map["grid"] = [row[:] for row in grid]
        existing_map["rows"] = rows
        existing_map["cols"] = cols
    else:
        new_map = {
            "name": cleaned_name,
            "grid": [row[:] for row in grid],
            "rows": rows,
            "cols": cols
        }
        maps.append(new_map)
        
    if save_custom_maps(maps):
        return cleaned_name
    return None

def delete_custom_map(name):
    maps = load_custom_maps()
    cleaned_name = name.strip().upper()
    updated_maps = [m for m in maps if m["name"].strip().upper() != cleaned_name]
    return save_custom_maps(updated_maps)
