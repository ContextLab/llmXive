"""
Configuration loader for the project.
Reads settings from code/config.yaml.
"""
import os
import sys
import yaml
from pathlib import Path
import logging

def load_config(config_path: str = None) -> dict:
    """
    Load configuration from a YAML file.
    Defaults to code/config.yaml if no path is provided.
    """
    if config_path is None:
        # Default path relative to this file
        config_path = Path(__file__).parent / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        # If config.yaml is missing, provide a minimal default or fail
        # For robustness, we return a minimal default if the file is missing
        # but log a warning.
        logging.warning(f"Config file {config_path} not found. Using defaults.")
        return {
            "alpha_band": [8, 12],
            "filter_band": [1, 40],
            "dataset_id": "ds000248",
            "electrodes": ["F3", "F4", "Fz", "P3", "P4", "Pz"]
        }

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if config is None:
        config = {}
        
    return config

def get_electrode_pairs(config: dict) -> list:
    """
    Generate frontal-parietal electrode pairs from config.
    """
    electrodes = config.get("electrodes", ["F3", "F4", "Fz", "P3", "P4", "Pz"])
    frontal = [e for e in electrodes if e.startswith('F')]
    parietal = [e for e in electrodes if e.startswith('P')]
    
    pairs = []
    for f in frontal:
        for p in parietal:
            pairs.append(f"{f}-{p}")
    return pairs
