"""
Script to verify T009: Setup environment configuration and logging infrastructure.

This script:
1. Loads config.yaml
2. Sets up the logger using utils.logging_handler
3. Logs a verification metric: reward_fidelity_level=dense
4. Verifies that logs/run.log contains the expected line.
"""
import os
import sys
from pathlib import Path
import yaml
import logging
import time
import re

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_handler import setup_logger, log_metric, load_config

def main():
    print("Starting T009 Verification: Environment Configuration and Logging...")
    
    # 1. Verify config.yaml exists and is valid
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("FAIL: config.yaml not found.")
        sys.exit(1)
    
    try:
        config = load_config()
        print(f"OK: config.yaml loaded successfully.")
    except Exception as e:
        print(f"FAIL: Error loading config.yaml: {e}")
        sys.exit(1)
    
    # 2. Setup logger
    logger = setup_logger("T009_Verification", config)
    print(f"OK: Logger setup complete. File handler -> {config['logging']['file_path']}")
    
    # 3. Log the specific metric required by T009
    fidelity_level = config.get('default_experiment', {}).get('reward_fidelity_level', 'dense')
    print(f"Logging metric: reward_fidelity_level={fidelity_level}")
    
    log_metric(
        logger,
        "reward_fidelity_level",
        fidelity_level,
        extra_data={"recovery_segment_id": "verification_test"}
    )
    
    # Force flush to ensure disk write
    for handler in logger.handlers:
        if hasattr(handler, 'flush'):
            handler.flush()
    
    # 4. Verify the log file contains the expected line
    log_path = Path(config['logging']['file_path'])
    if not log_path.exists():
        print(f"FAIL: Log file {log_path} was not created.")
        sys.exit(1)
    
    time.sleep(0.1) # Brief delay to ensure file system sync
    
    content = log_path.read_text()
    search_pattern = r"reward_fidelity_level=dense"
    
    if re.search(search_pattern, content):
        print(f"SUCCESS: Log file {log_path} contains 'reward_fidelity_level=dense'.")
        print("T009 Verification PASSED.")
        return True
    else:
        print(f"FAIL: Log file {log_path} does not contain 'reward_fidelity_level=dense'.")
        print("Content preview:")
        print(content[-500:]) # Print last 500 chars
        sys.exit(1)

if __name__ == "__main__":
    main()
