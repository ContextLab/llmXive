import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
import logging
import yaml

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Global configuration constants
VARIANCE_THRESHOLD = 100.0
RANDOM_SEED = 42
DATA_SOURCE = "oqmd"

def parse_cli_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Alloy Design Pipeline")
    
    # Generic paths
    parser.add_argument('--input-path', type=str, help='Input data file path')
    parser.add_argument('--output-path', type=str, help='Output data file path')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    
    # US3 Specific
    parser.add_argument('--variance-threshold', type=float, default=None, 
                        help='Threshold for flagging high variance regions (FR-006)')
    parser.add_argument('--run-sensitivity', action='store_true', help='Run sensitivity analysis')
    
    # US2 Specific (for potential future use in this module if needed)
    parser.add_argument('--model-path', type=str, help='Path to trained models')
    
    args = parser.parse_args()
    return args

def load_environment():
    """Load environment variables from .env file and config_default.yaml.
    
    Gracefully handles missing .env files by loading defaults from config_default.yaml.
    Exposes variance_threshold, random_seed, and data_source as global constants.
    """
    # Attempt to load .env file
    env_path = Path(os.getcwd()) / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        logger.info(f"Environment variables loaded from {env_path}")
    else:
        logger.warning(f"No .env file found at {env_path}. Loading defaults from config_default.yaml.")
        _load_defaults_from_yaml()
    
    # Update global constants from environment variables if present
    global VARIANCE_THRESHOLD, RANDOM_SEED, DATA_SOURCE
    
    env_var = os.getenv('VARIANCE_THRESHOLD')
    if env_var is not None:
        try:
            VARIANCE_THRESHOLD = float(env_var)
            logger.info(f"VARIANCE_THRESHOLD set to {VARIANCE_THRESHOLD} from environment")
        except ValueError:
            logger.warning(f"Invalid VARIANCE_THRESHOLD value '{env_var}', using default {VARIANCE_THRESHOLD}")
    
    env_seed = os.getenv('RANDOM_SEED')
    if env_seed is not None:
        try:
            RANDOM_SEED = int(env_seed)
            logger.info(f"RANDOM_SEED set to {RANDOM_SEED} from environment")
        except ValueError:
            logger.warning(f"Invalid RANDOM_SEED value '{env_seed}', using default {RANDOM_SEED}")
    
    env_source = os.getenv('DATA_SOURCE')
    if env_source is not None:
        DATA_SOURCE = env_source
        logger.info(f"DATA_SOURCE set to {DATA_SOURCE} from environment")

def _load_defaults_from_yaml():
    """Load default configuration from config_default.yaml."""
    config_path = Path(os.getcwd()) / 'config_default.yaml'
    
    if not config_path.exists():
        logger.warning("No config_default.yaml found. Using hardcoded defaults.")
        return
    
    try:
        with open(config_path, 'r') as f:
            defaults = yaml.safe_load(f)
        
        if defaults:
            global VARIANCE_THRESHOLD, RANDOM_SEED, DATA_SOURCE
            
            if 'variance_threshold' in defaults:
                VARIANCE_THRESHOLD = float(defaults['variance_threshold'])
                logger.info(f"VARIANCE_THRESHOLD loaded from config_default.yaml: {VARIANCE_THRESHOLD}")
            
            if 'random_seed' in defaults:
                RANDOM_SEED = int(defaults['random_seed'])
                logger.info(f"RANDOM_SEED loaded from config_default.yaml: {RANDOM_SEED}")
            
            if 'data_source' in defaults:
                DATA_SOURCE = defaults['data_source']
                logger.info(f"DATA_SOURCE loaded from config_default.yaml: {DATA_SOURCE}")
    except Exception as e:
        logger.error(f"Failed to load config_default.yaml: {e}")

def get_config():
    """Get configuration from environment or defaults.
    
    Returns a dictionary containing the current configuration values.
    """
    return {
        'variance_threshold': VARIANCE_THRESHOLD,
        'random_seed': RANDOM_SEED,
        'data_source': DATA_SOURCE,
        'data_dir': os.getenv('DATA_DIR', 'data'),
        'processed_dir': os.getenv('PROCESSED_DIR', 'data/processed'),
    }

def verify_config(config: dict):
    """Verify that required configuration is present."""
    required_keys = ['variance_threshold', 'random_seed', 'data_source']
    missing = [k for k in required_keys if k not in config]
    if missing:
        raise ValueError(f"Missing required configuration keys: {missing}")
    
    # Validate types
    if not isinstance(config['variance_threshold'], (int, float)):
        raise TypeError("variance_threshold must be a number")
    if not isinstance(config['random_seed'], int):
        raise TypeError("random_seed must be an integer")
    if not isinstance(config['data_source'], str):
        raise TypeError("data_source must be a string")
    
    logger.info("Configuration verified successfully")
