"""
VoiceGrab Config Schema
Loads defaults from config_default.json (single source of truth)
"""

import json
import copy
from pathlib import Path

# Load default configuration from config_default.json (SINGLE SOURCE OF TRUTH)
def _load_default_config():
    """Load defaults from config_default.json"""
    default_path = Path(__file__).parent / "config_default.json"
    if default_path.exists():
        try:
            with open(default_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config_default.json: {e}")
    # Minimal fallback if file missing
    return {
        "version": "2.3.0",
        "api": {"key": "", "provider": "groq", "model": "whisper-large-v3"},
        "input": {"mode": "toggle", "hotkey": "ctrl r"},
        "global": {"save_audio": False, "max_duration": 180, "default_mode": "ai", "active_mode": "ai"},
        "modes": {},
        "ui": {"floating_indicator": True}
    }

DEFAULT_CONFIG = _load_default_config()


class Config:
    """Configuration manager with defaults and reset capability"""
    
    def __init__(self, config_path: str = None):
        if config_path:
            self.path = Path(config_path)
        else:
            # Config next to this script
            self.path = Path(__file__).parent / "config.json"
        
        self._config = None
        self._defaults = copy.deepcopy(DEFAULT_CONFIG)
    
    def exists(self) -> bool:
        """Check if config file exists"""
        return self.path.exists()
    
    def load(self) -> dict:
        """Load config from file or return defaults"""
        if self.exists():
            try:
                with open(self.path, 'r', encoding='utf-8-sig') as f:
                    self._config = json.load(f)
                # Merge with defaults for missing keys
                self._config = self._merge_defaults(self._config)
            except Exception as e:
                print(f"Error loading config: {e}")
                self._config = copy.deepcopy(self._defaults)
        else:
            self._config = copy.deepcopy(self._defaults)
        return self._config
    
    def save(self, config: dict = None) -> bool:
        """Save config to file"""
        if config:
            self._config = config
        
        # CRITICAL: Validate config before saving to prevent data loss
        if not self._config:
            print(f"[CONFIG ERROR] Attempted to save NULL config - REFUSED!")
            return False
        
        json_str = json.dumps(self._config, ensure_ascii=False, indent=2)
        if len(json_str) < 50:
            print(f"[CONFIG ERROR] Config too small ({len(json_str)} chars) - REFUSED!")
            return False
        
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Get config value by dot notation (e.g., 'api.key')"""
        if self._config is None:
            self.load()
        
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value):
        """Set config value by dot notation"""
        if self._config is None:
            self.load()
        
        keys = key.split('.')
        obj = self._config
        for k in keys[:-1]:
            if k not in obj:
                obj[k] = {}
            obj = obj[k]
        obj[keys[-1]] = value
    
    def reset_to_defaults(self, section: str = None) -> dict:
        """Reset config to defaults (all or specific section)"""
        if section:
            if section in self._defaults:
                self._config[section] = copy.deepcopy(self._defaults[section])
        else:
            self._config = copy.deepcopy(self._defaults)
        return self._config
    
    def get_defaults(self, section: str = None) -> dict:
        """Get default values"""
        if section and section in self._defaults:
            return copy.deepcopy(self._defaults[section])
        return copy.deepcopy(self._defaults)
    
    def _merge_defaults(self, config: dict) -> dict:
        """Merge loaded config with defaults for missing keys"""
        result = copy.deepcopy(self._defaults)
        self._deep_update(result, config)
        return result
    
    def _deep_update(self, base: dict, update: dict):
        """Recursively update base dict with update dict"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value


# Singleton instance
_config_instance = None

def get_config(config_path: str = None) -> Config:
    """Get or create config instance"""
    global _config_instance
    if _config_instance is None or config_path:
        _config_instance = Config(config_path)
    return _config_instance


if __name__ == "__main__":
    # Test
    config = Config()
    print("Default config:")
    print(json.dumps(config.load(), ensure_ascii=False, indent=2))
