import os
from pathlib import Path
from typing import Optional, Dict, Any
import json

class Config:
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        if config_dict:
            self._config = config_dict
        else:
            self._config = self._load_default()
    
    def _load_default(self) -> Dict[str, Any]:
        base = Path(__file__).resolve().parent.parent.parent
        return {
            'paths': {
                'project_root': str(base),
                'raw_data': str(base / 'data' / 'raw'),
                'derived_data': str(base / 'data' / 'derived'),
                'output_dir': str(base / 'docs' / 'output'),
                'figures_dir': str(base / 'figures')
            },
            'api': {
                'github_token': os.getenv('GITHUB_TOKEN', ''),
                'base_url': 'https://api.github.com'
            }
        }

    def __getitem__(self, key):
        return self._config[key]
    
    def __contains__(self, key):
        return key in self._config

def get_config() -> Config:
    return Config()
