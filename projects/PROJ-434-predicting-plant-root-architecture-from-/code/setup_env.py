"""
Environment configuration management for the root architecture prediction pipeline.

This module handles:
1. Loading .env files via python-dotenv
2. Validating required environment variables
3. Creating a default .env.example file if missing
4. Centralized configuration access
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Ensure utils is in path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import load_environment, get_env, Config, validate_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ENV_FILE_PATH = Path(__file__).resolve().parent.parent / '.env'
ENV_EXAMPLE_PATH = Path(__file__).resolve().parent.parent / '.env.example'

# Define required environment variables for this project
# Currently, no external API keys are strictly required for the core pipeline
# (SoilGrids data is public, trait data is from local files or public repos).
# However, we define placeholders for potential future API usage (e.g., Zenodo token).
REQUIRED_VARS: List[str] = [
    # "ZENODO_API_TOKEN",  # Optional: for authenticated downloads
    "RUN_MODE",             # Required: 'production' or 'test'
    "RANDOM_SEED",          # Required: integer for reproducibility
]

DEFAULT_ENV_VALUES: Dict[str, str] = {
    "RUN_MODE": "production",
    "RANDOM_SEED": "42",
}

def create_default_env_file() -> bool:
    """
    Creates a .env.example file with documentation and default values if it doesn't exist.
    Returns True if successful, False otherwise.
    """
    try:
        if ENV_EXAMPLE_PATH.exists():
            logger.info(f"Example env file already exists at {ENV_EXAMPLE_PATH}")
            return True

        content = [
            "# Environment Configuration for Root Architecture Prediction Pipeline",
            "# Copy this file to .env and fill in your values.",
            "",
            "# Execution Mode",
            "# Options: 'production' (strict real-data enforcement), 'test' (allows synthetic fallbacks)",
            "RUN_MODE=production",
            "",
            "# Random Seed for Reproducibility",
            "RANDOM_SEED=42",
            "",
            "# Optional: Zenodo API Token for authenticated downloads",
            "# ZENODO_API_TOKEN=your_token_here",
            ""
        ]

        with open(ENV_EXAMPLE_PATH, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

        logger.info(f"Created example env file at {ENV_EXAMPLE_PATH}")
        return True

    except Exception as e:
        logger.error(f"Failed to create example env file: {e}")
        return False

def validate_required_env_vars() -> Tuple[bool, List[str]]:
    """
    Validates that all required environment variables are set.
    Returns (is_valid, list_of_missing_vars).
    """
    missing = []
    for var in REQUIRED_VARS:
        if var not in os.environ or not os.environ[var]:
            missing.append(var)
    
    if missing:
        logger.error(f"Missing required environment variables: {missing}")
        return False, missing
    
    logger.info("All required environment variables are present.")
    return True, []

def main() -> int:
    """
    Main entry point for environment setup and validation.
    Loads the .env file, validates required variables, and creates .env.example if missing.
    
    Returns:
        0: Success
        1: Validation failure
    """
    logger.info("Starting environment configuration setup...")

    # 1. Ensure .env.example exists
    create_default_env_file()

    # 2. Load .env file if it exists
    if ENV_FILE_PATH.exists():
        logger.info(f"Loading environment from {ENV_FILE_PATH}")
        load_dotenv(ENV_FILE_PATH)
    else:
        logger.warning(f"No .env file found at {ENV_FILE_PATH}. Using system environment variables.")

    # 3. Validate required variables
    is_valid, missing = validate_required_env_vars()
    if not is_valid:
        logger.error("Environment validation failed. Please set the missing variables.")
        return 1

    # 4. Initialize Config object (optional, for downstream usage)
    try:
        config = load_environment()
        logger.info(f"Configuration loaded successfully. RUN_MODE: {config.run_mode}, RANDOM_SEED: {config.random_seed}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1

    logger.info("Environment configuration setup completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
