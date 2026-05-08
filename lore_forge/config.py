"""Simple JSON-backed key-value store for app settings."""

import json
from .constants import DATA_DIR, CONFIG_FILE


class ConfigManager:
    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        self._data = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    self._data = json.load(f)
            except Exception:
                pass

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        with open(CONFIG_FILE, "w") as f:
            json.dump(self._data, f, indent=2)
