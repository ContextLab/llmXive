import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
import logging

from utils.logging_config import get_logger

logger = get_logger(__name__)

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
    """Load environment variables from .env file."""
    load_dotenv()
    logger.info("Environment variables loaded from .env")

def get_config():
    """Get configuration from environment or defaults."""
    config = {
        'variance_threshold': float(os.getenv('VARIANCE_THRESHOLD', 100.0)),
        'random_seed': int(os.getenv('RANDOM_SEED', 42)),
        'data_dir': os.getenv('DATA_DIR', 'data'),
        'processed_dir': os.getenv('PROCESSED_DIR', 'data/processed'),
    }
    return config

def verify_config(config: dict):
    """Verify that required configuration is present."""
    required_keys = ['variance_threshold', 'random_seed', 'data_dir']
    missing = [k for k in required_keys if k not in config]
    if missing:
        raise ValueError(f"Missing required configuration keys: {missing}")
    logger.info("Configuration verified successfully")
