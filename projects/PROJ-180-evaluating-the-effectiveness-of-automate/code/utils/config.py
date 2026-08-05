import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_config() -> Dict[str, Any]:
    """Get the main configuration dictionary."""
    return {
        'github_token': os.getenv('GITHUB_TOKEN'),
        'github_api_base_url': os.getenv('GITHUB_API_BASE_URL', 'https://api.github.com'),
        'data_root': Path(os.getenv('DATA_ROOT', 'data')),
        'code_root': Path(os.getenv('CODE_ROOT', 'code')),
        'results_root': Path(os.getenv('RESULTS_ROOT', 'results')),
        'specs_root': Path(os.getenv('_SPECS_ROOT', 'specs')),
        'max_repos': int(os.getenv('MAX_REPOS', '40')),
        'retry_count': int(os.getenv('RETRY_COUNT', '2')),
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    }

def load_env():
    """Load environment variables from .env file."""
    load_dotenv()
    logger.debug("Environment variables loaded")

def get_github_token() -> str:
    """Get GitHub token from environment."""
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    return token

def get_github_api_base_url() -> str:
    """Get GitHub API base URL."""
    return os.getenv('GITHUB_API_BASE_URL', 'https://api.github.com')

def get_data_raw_dir() -> Path:
    """Get path to data/raw directory."""
    return get_config()['data_root'] / 'raw'

def get_data_processed_dir() -> Path:
    """Get path to data/processed directory."""
    return get_config()['data_root'] / 'processed'

def get_data_acquired_dir() -> Path:
    """Get path to data/acquired directory (intermediate storage)."""
    return get_config()['data_root'] / 'acquired'

def get_results_dir() -> Path:
    """Get path to results directory."""
    return get_config()['results_root']

def get_specs_dir() -> Path:
    """Get path to specs directory."""
    return get_config()['specs_root']

def get_code_dir() -> Path:
    """Get path to code directory."""
    return get_config()['code_root']

def get_max_repos() -> int:
    """Get maximum number of repositories to process."""
    return get_config()['max_repos']

def get_retry_count() -> int:
    """Get retry count for failed operations."""
    return get_config()['retry_count']

def get_log_level() -> str:
    """Get log level."""
    return get_config()['log_level']

def validate_paths():
    """Validate that all required directories exist."""
    config = get_config()
    required_dirs = [
        config['data_root'],
        get_data_raw_dir(),
        get_data_processed_dir(),
        get_data_acquired_dir(),
        config['results_root'],
        config['specs_root'],
        config['code_root']
    ]
    
    for path in required_dirs:
        if not path.exists():
            logger.warning(f"Directory does not exist: {path}")
        else:
            logger.debug(f"Directory exists: {path}")

def main():
    """Main entry point for config validation."""
    validate_paths()
    logger.info("Configuration validated successfully")

if __name__ == "__main__":
    main()
