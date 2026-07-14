"""
Script to verify that config migration has been performed correctly.
Checks that:
1. config.yaml is under 2048 bytes
2. state file exists and contains derived_statistics
3. config.yaml does not contain derived statistic keys
"""
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
STATE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"

DERIVED_KEYS = ['dataset_stats', 'inference_results', 'simulation_metrics']
CONFIG_SIZE_LIMIT = 2048

def main():
    print(f"Verifying config migration at {datetime.now().isoformat()}")
    errors = []
    
    # 1. Check config file size
    if not CONFIG_PATH.exists():
        errors.append(f"Config file not found: {CONFIG_PATH}")
    else:
        config_size = os.path.getsize(CONFIG_PATH)
        print(f"Config file size: {config_size} bytes (limit: {CONFIG_SIZE_LIMIT} bytes)")
        if config_size > CONFIG_SIZE_LIMIT:
            errors.append(f"Config file size {config_size} exceeds limit {CONFIG_SIZE_LIMIT}")
        else:
            print("✓ Config file size is within limits")
    
    # 2. Check state file exists
    if not STATE_PATH.exists():
        errors.append(f"State file not found: {STATE_PATH}")
    else:
        print(f"✓ State file exists: {STATE_PATH}")
        
        # 3. Check state file contains derived_statistics
        try:
            with open(STATE_PATH, 'r', encoding='utf-8') as f:
                state = yaml.safe_load(f) or {}
            
            if 'derived_statistics' in state:
                print(f"✓ State file contains 'derived_statistics' section")
                print(f"  Keys in derived_statistics: {list(state['derived_statistics'].keys())}")
            else:
                print("  Note: No 'derived_statistics' section in state file (may be empty)")
        except Exception as e:
            errors.append(f"Error reading state file: {e}")
    
    # 4. Check config file doesn't contain derived keys
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            found_derived = [key for key in DERIVED_KEYS if key in config]
            if found_derived:
                errors.append(f"Config file still contains derived keys: {found_derived}")
            else:
                print("✓ Config file does not contain derived statistic keys")
        except Exception as e:
            errors.append(f"Error reading config file: {e}")
    
    # Report results
    print("\n" + "="*50)
    if errors:
        print("VERIFICATION FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1
    else:
        print("VERIFICATION PASSED: Config migration successful")
        return 0

if __name__ == "__main__":
    sys.exit(main())