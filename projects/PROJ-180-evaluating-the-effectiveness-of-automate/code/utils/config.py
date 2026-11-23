import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_config() -> Dict[str, Any]:
    """Load configuration from code/config.yaml."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    
    if not config_path.exists():
        logger.warning(f"config.yaml not found at {config_path}, using defaults")
        return {
            'data_raw_dir': 'data/raw',
            'data_processed_dir': 'data/processed',
            'results_dir': 'results',
            'max_repos': 30,
            'retry_count': 2,
            'log_level': 'INFO'
        }
    
    # Simple YAML parser for basic configuration
    config = {}
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    config[key.strip()] = value.strip().strip('"').strip("'")
    
    return config

def load_env() -> None:
    """Load environment variables from .env file."""
    load_dotenv()

def get_github_token() -> Optional[str]:
    """Get GitHub token from environment."""
    return os.getenv('GITHUB_TOKEN')

def get_github_api_base_url() -> str:
    """Get GitHub API base URL."""
    return os.getenv('GITHUB_API_URL', 'https://api.github.com')

def get_data_raw_dir() -> Path:
    """Get path to raw data directory."""
    config = get_config()
    raw_dir = config.get('data_raw_dir', 'data/raw')
    return Path(__file__).parent.parent.parent / raw_dir

def get_data_processed_dir() -> Path:
    """Get path to processed data directory."""
    config = get_config()
    processed_dir = config.get('data_processed_dir', 'data/processed')
    return Path(__file__).parent.parent.parent / processed_dir

def get_data_acquired_dir() -> Path:
    """Get path to acquired data directory."""
    return get_data_raw_dir()

def get_results_dir() -> Path:
    """Get path to results directory."""
    config = get_config()
    results_dir = config.get('results_dir', 'results')
    return Path(__file__).parent.parent.parent / results_dir

def get_specs_dir() -> Path:
    """Get path to specs directory."""
    return Path(__file__).parent.parent.parent / 'specs'

def get_code_dir() -> Path:
    """Get path to code directory."""
    return Path(__file__).parent.parent

def get_max_repos() -> int:
    """Get maximum number of repositories to process."""
    config = get_config()
    return int(config.get('max_repos', 30))

def get_retry_count() -> int:
    """Get retry count for failed operations."""
    config = get_config()
    return int(config.get('retry_count', 2))

def get_log_level() -> str:
    """Get logging level."""
    config = get_config()
    return config.get('log_level', 'INFO')

def validate_paths() -> bool:
    """Validate that all required directories exist."""
    dirs = [
        get_data_raw_dir(),
        get_data_processed_dir(),
        get_results_dir(),
        get_specs_dir(),
        get_code_dir()
    ]
    
    for dir_path in dirs:
        if not dir_path.exists():
            logger.warning(f"Directory does not exist: {dir_path}")
            return False
    
    return True

def main():
    """Main entry point for config validation."""
    if validate_paths():
        print("All paths validated successfully")
    else:
        print("Path validation failed")

if __name__ == "__main__":
    main()
