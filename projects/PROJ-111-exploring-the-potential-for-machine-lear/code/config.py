import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
from dotenv import load_dotenv

class Config:
    """Configuration class for the project."""
    def __init__(self):
        load_dotenv()
        self.seed = int(os.getenv("RANDOM_SEED", "42"))
        self.data_dir = os.getenv("DATA_DIR", "data")
        self.log_dir = os.getenv("LOG_DIR", "logs")
        self.model_dir = os.getenv("MODEL_DIR", "models")
        self.results_dir = os.getenv("RESULTS_DIR", "results")
        
        # Data generation parameters
        self.J1 = float(os.getenv("J1_COUPING", "1.0"))
        self.J2 = float(os.getenv("J2_COUPING", "0.5"))
        self.n_steps = int(os.getenv("N_MC_STEPS", "1000"))
        self.batch_size = int(os.getenv("BATCH_SIZE", "32"))
        
        # Logging level
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

_config_instance: Optional[Config] = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reset_config():
    global _config_instance
    _config_instance = None

def save_config_to_json(filepath: str):
    config = get_config()
    config_dict = {
        "seed": config.seed,
        "data_dir": config.data_dir,
        "log_dir": config.log_dir,
        "model_dir": config.model_dir,
        "results_dir": config.results_dir,
        "J1": config.J1,
        "J2": config.J2,
        "n_steps": config.n_steps,
        "batch_size": config.batch_size,
        "log_level": config.log_level
    }
    with open(filepath, 'w') as f:
        json.dump(config_dict, f, indent=2)
    logging.info(f"Configuration saved to {filepath}")
