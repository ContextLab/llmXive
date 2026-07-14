import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List, Union

class ConfigError(Exception):
    pass

class Config:
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict

    def get(self, *keys, default=None):
        val = self._config
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
            if val is None:
                return default
        return val

def load_config(config_path: str = "config.yaml") -> Config:
    if not Path(config_path).exists():
        # Create a default config if none exists
        default_config = {
            'paths': {
                'genomic_input': 'data/raw/genomic_vcf.json',
                'env_input': 'data/raw/env_data.json',
                'compound_input': 'data/raw/compound_data.json',
                'genomic_output': 'data/raw/genomic_vcf.json',
                'env_output': 'data/raw/env_data.json',
                'compound_output': 'data/raw/compound_data.json',
                'filtered_output': 'data/processed/filtered.csv',
                'vif_output': 'data/processed/features_vif.csv',
                'state_file': 'state/PROJ-475-predicting-plant-defense-compound-produc.yaml'
            },
            'verified_urls': {
                'genomic': None,
                'env': None,
                'compound': None
            },
            'model': {
                'alpha': 0.1,
                'cv_folds': 5
            }
        }
        Path("config.yaml").parent.mkdir(parents=True, exist_ok=True)
        with open("config.yaml", 'w') as f:
            yaml.dump(default_config, f)
        return Config(default_config)
    
    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)
    return Config(config_dict)

def get_config() -> Config:
    return load_config()