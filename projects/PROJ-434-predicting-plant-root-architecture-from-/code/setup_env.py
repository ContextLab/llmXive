"""
Environment configuration management setup script.

This script initializes the .env file and validates environment variables
required for the plant root architecture prediction pipeline.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Attempt to import dotenv, provide helpful error if missing
try:
    from dotenv import load_dotenv
except ImportError:
    print("ERROR: python-dotenv is not installed.")
    print("Please install it via: pip install python-dotenv")
    print("It should be listed in code/requirements.txt")
    sys.exit(1)

from utils.config import load_environment, get_env, Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_default_env_file(env_path: Path) -> bool:
    """
    Create a default .env file if it doesn't exist.
    
    Args:
        env_path: Path to the .env file
        
    Returns:
        True if file was created, False if it already existed
    """
    if env_path.exists():
        logger.info(f".env file already exists at {env_path}")
        return False
    
    default_content = """# Environment Configuration for Plant Root Architecture Prediction Pipeline
# This file is loaded by setup_env.py and should be committed to version control
# with default values, but sensitive values should be overridden locally.

# Run Mode: 'production' (default) or 'test'
# In production mode, data loaders will fail if real data fetch fails.
# In test mode, synthetic fallbacks may be used for pipeline structure testing.
RUN_MODE=production

# Random seed for reproducibility
RANDOM_SEED=42

# SoilGrids API (if using direct API access instead of local files)
# SOILGRIDS_API_KEY=your_api_key_here

# Logging level
LOG_LEVEL=INFO

# Data paths (relative to project root)
DATA_RAW_DIR=data/raw
DATA_PROCESSED_DIR=data/processed
DATA_LOGS_DIR=data/logs
FIGURES_DIR=figures
ARTIFACTS_DIR=artifacts

# Model configuration
MODEL_TYPE=random_forest
N_ESTIMATORS=100
MAX_DEPTH=None

# Validation parameters
LOSO_ENABLED=True
STRATIFIED_K_FOLD_ENABLED=True
K_FOLD_K=5

# Permutation test parameters
N_PERMUTATIONS=100
PERMUTATION_SEED=42

# Data quality thresholds
MIN_MATCH_PROPORTION=0.90
MIN_OBSERVATIONS_PER_SPECIES=10

# Feature importance significance threshold
SIGNIFICANCE_THRESHOLD=0.05
"""
    
    try:
        env_path.write_text(default_content)
        logger.info(f"Created default .env file at {env_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to create .env file: {e}")
        return False

def validate_required_env_vars(required_vars: Dict[str, Any]) -> bool:
    """
    Validate that required environment variables are set.
    
    Args:
        required_vars: Dictionary of required variable names and their types
        
    Returns:
        True if all required variables are valid, False otherwise
    """
    all_valid = True
    for var_name, var_type in required_vars.items():
        value = os.getenv(var_name)
        if value is None:
            logger.warning(f"Environment variable '{var_name}' is not set")
            all_valid = False
            continue
        
        # Type validation
        if var_type == bool:
            if value.lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                logger.error(f"Environment variable '{var_name}' has invalid boolean value: {value}")
                all_valid = False
        elif var_type == int:
            try:
                int(value)
            except ValueError:
                logger.error(f"Environment variable '{var_name}' has invalid integer value: {value}")
                all_valid = False
        elif var_type == float:
            try:
                float(value)
            except ValueError:
                logger.error(f"Environment variable '{var_name}' has invalid float value: {value}")
                all_valid = False
        
        logger.info(f"Validated '{var_name}': {value}")
    
    return all_valid

def main():
    """Main entry point for environment setup."""
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / '.env'
    
    logger.info("Starting environment configuration setup...")
    
    # Load existing environment variables
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"Loaded existing .env file from {env_path}")
    else:
        logger.info("No .env file found, creating default...")
        create_default_env_file(env_path)
        load_dotenv(env_path)
    
    # Validate critical environment variables
    required_vars = {
        'RUN_MODE': str,
        'RANDOM_SEED': int,
        'LOG_LEVEL': str,
        'DATA_RAW_DIR': str,
        'DATA_PROCESSED_DIR': str,
        'DATA_LOGS_DIR': str,
        'FIGURES_DIR': str,
        'ARTIFACTS_DIR': str,
        'MIN_MATCH_PROPORTION': float,
        'MIN_OBSERVATIONS_PER_SPECIES': int,
        'SIGNIFICANCE_THRESHOLD': float,
    }
    
    is_valid = validate_required_env_vars(required_vars)
    
    if not is_valid:
        logger.error("Environment validation failed. Please check the .env file.")
        sys.exit(1)
    
    # Load and display configuration
    config = load_environment()
    logger.info("Environment configuration loaded successfully:")
    logger.info(f"  RUN_MODE: {config.get('RUN_MODE')}")
    logger.info(f"  RANDOM_SEED: {config.get('RANDOM_SEED')}")
    logger.info(f"  LOG_LEVEL: {config.get('LOG_LEVEL')}")
    logger.info(f"  Data directories configured: {len([k for k in config.keys() if 'DIR' in k])}")
    
    logger.info("Environment setup complete.")
    return 0

if __name__ == '__main__':
    sys.exit(main())