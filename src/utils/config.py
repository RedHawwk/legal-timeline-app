import yaml
from typing import Dict, Any
from pathlib import Path

class Config:
    """Configuration management class"""

    def __init__(self, config_data: Dict[str, Any]):
        self.data = config_data

    @classmethod
    def load(cls, config_path: str) -> 'Config':
        """Load configuration from YAML file"""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")

        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)

        return cls(config_data)

    def get(self, key: str, default=None):
        """Get configuration value using dot notation (e.g., 'processing.max_workers')"""
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value