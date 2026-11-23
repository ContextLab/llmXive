"""
Standalone script to demonstrate and validate the configuration loading system (T007).

This script loads the config.yaml, applies environment overrides, and prints the result.
It serves as a verification step for the configuration management setup.

Usage:
    python code/config_loader.py
"""
import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils import load_config, setup_logging

def main():
    # Setup logging first to ensure we can log config loading status
    logger = setup_logging("INFO")
    logger.info("Starting configuration loading process...")

    try:
        # Load configuration
        config = load_config()
        
        logger.info(f"Configuration loaded successfully.")
        logger.info(f"Project Name: {config.get('project', {}).get('name', 'N/A')}")
        logger.info(f"Log Level: {config.get('logging', {}).get('level', 'N/A')}")
        
        # Validate critical keys exist
        required_keys = ['project', 'logging', 'data', 'apis', 'analysis']
        missing_keys = [k for k in required_keys if k not in config]
        
        if missing_keys:
            logger.warning(f"Missing required configuration sections: {missing_keys}")
        else:
            logger.info("All required configuration sections present.")

        # Print summary of data paths
        data_config = config.get('data', {})
        logger.info(f"Data Raw Dir: {data_config.get('raw_dir', 'N/A')}")
        logger.info(f"Data Processed Dir: {data_config.get('processed_dir', 'N/A')}")

        return 0

    except Exception as e:
        logger.error(f"Failed to load configuration: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())