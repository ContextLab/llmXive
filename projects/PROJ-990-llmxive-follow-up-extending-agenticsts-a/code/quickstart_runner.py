import os
import sys
import json
import logging
import time
import traceback
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import run_full_pipeline
from config import load_config_from_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('llmXive.quickstart_runner')

def check_file_exists(path: str) -> bool:
    return os.path.exists(path)

def load_json_safe(path: str) -> dict:
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return {}

def run_quickstart_validation():
    """
    Execute the full pipeline as defined in quickstart.md.
    This ensures all artifacts are generated.
    """
    logger.info("Starting Quickstart Validation...")
    start_time = time.time()
    
    config_path = 'config.json'
    if not check_file_exists(config_path):
        logger.error(f"Config file {config_path} not found.")
        return False

    config = load_json_safe(config_path)
    
    try:
        run_full_pipeline(config)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        traceback.print_exc()
        return False
    
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Quickstart validation completed in {duration:.2f} seconds.")
    
    # Verify key outputs exist
    required_files = [
        'data/processed/simulation_logs_dynamic.json',
        'data/processed/simulation_logs_static.json',
        'data/processed/simulation_logs_random.json',
        'data/processed/statistical_results.json'
    ]
    
    all_present = True
    for f in required_files:
        if not check_file_exists(f):
            logger.warning(f"Missing required output: {f}")
            all_present = False
    
    return all_present

def main():
    success = run_quickstart_validation()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
