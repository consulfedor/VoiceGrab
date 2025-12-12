"""
VoiceGrab Config Schema
Defines default configuration and validation
"""

import json
import copy
from pathlib import Path

# Default configuration - can be reset to this
DEFAULT_CONFIG = {
    "version": "1.0",
    
    "api": {
        "key": "",
        "provider": "groq",
        "model": "whisper-large-v3"
    },
    
    "input": {
        "mode": "toggle",  # toggle or hold
        "hotkey": "alt gr",
        "mode_switch": "hotkeys",  # hotkeys, cycle, fixed
        "cycle_hotkey": "alt gr+tab",  # for cycle mode
        "mode_hotkeys": {
            "ai": "alt gr+1",
            "code": "alt gr+2",
            "docs": "alt gr+3",
            "notes": "alt gr+4",
            "empty": "alt gr+5"
        }
    },
    
    "recording": {
        "max_duration": 180,
        "min_duration": 0.5,
        "sample_rate": 16000
    },
    
    "modes": {
        "default": "ai",
        "templates": {
            "ai": {
                "name": "🤖 AI Chat",
                "description": "Промпты для Claude, GPT, Gemini",
                "prompt": "Формулировка промпта для AI ассистента. Русский язык, английские технические термины допустимы.",
                "censor": False,
                "cleanup": True
            },
            "code": {
                "name": "💻 Code",
                "description": "Программирование и архитектура",
                "prompt": "Программирование, Python, JavaScript, API, Docker, Git. Технический контекст, русский с английскими терминами.",
                "censor": False,
                "cleanup": True
            },
            "docs": {
                "name": "📋 Docs",
                "description": "Документация и спецификации",
                "prompt": "Техническая документация, ТЗ, спецификации. Формальный русский язык.",
                "censor": False,
                "cleanup": True
            },
            "notes": {
                "name": "📝 Notes",
                "description": "Заметки для Obsidian, NotebookLM",
                "prompt": "Заметки, мысли, идеи. Структурировать по пунктам если уместно.",
                "censor": False,
                "cleanup": True
            },
            "empty": {
                "name": "💬 Custom",
                "description": "Пустой шаблон для своего",
                "prompt": "",
                "censor": False,
                "cleanup": False
            }
        }
    },
    
    "cleanup": {
        "enabled": True,
        "use_prompt": True,
        "use_regex": True,
        "filler_words": [
            "эм", "ээ", "ну", "типа", "как бы", 
            "короче", "в общем", "значит", "ну типа",
            "блин", "вот"
        ],
        "garbage_phrases": [
            "Продолжение следует",
            "продолжение следует",
            "Subtitles by",
            "Subscribe",
            "Thank you for watching",
            "Спасибо за просмотр",
            "Подписывайтесь"
        ]
    },
    
    "language": {
        "primary": "ru",
        "allow_english": True
    },
    
    "ui": {
        "floating_indicator": True,
        "show_timer": True,
        "show_mode": True,
        "preview_length": 100
    },
    
    "storage": {
        "save_audio": "never",  # never, session, always
        "audio_dir": "recordings",  # relative to script dir
        "log_transcriptions": "always",  # never, session, always
        "log_file": "transcriptions.log"  # relative to script dir
    },
    
    "shortcuts": {
        "create_desktop": False
    }
}


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
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
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
