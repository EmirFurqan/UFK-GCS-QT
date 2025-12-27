
import json
import os
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent / "connection_settings.json"

DEFAULT_SETTINGS = {
    "plane_connection_type": "udp",    # 'udp' or 'serial'
    "plane_port": "14550",
    "plane_address": "0.0.0.0",
    "plane_serial_port": "/dev/ttyUSB0",
    "plane_baud": "57600",
    "camera_port": "5000",
    "server_address": "http://10.1.36.78:8000",
    "server_username": "",
    "server_password": ""
}

class SettingsManager:
    @staticmethod
    def load_settings():
        if not SETTINGS_FILE.exists():
            return DEFAULT_SETTINGS.copy()
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Merge with defaults to ensure all keys exist
                settings = DEFAULT_SETTINGS.copy()
                settings.update(data)
                return settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            return DEFAULT_SETTINGS.copy()

    @staticmethod
    def save_settings(settings):
        try:
            # Ensure directory exists
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
