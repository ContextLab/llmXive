"""
Verification script for Task T022.
Verifies that T021 correctly logs progress and memory usage to data/processed/memory_profile.json
and that the output CSV matches the schema defined in specs/001-lm-axive-noise-injection/contracts/.
"""
import os
import sys
import json
import csv
import logging
from pathlib import Path

# Add project root to path if not already present
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import OutputPaths
from memory_monitor import save_memory_profile

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verify_baseline")

# Constants based on schema contracts
BASELINE_CSV_PATH = "data/processed/baseline_vectors.csv"
MEMORY_JSON_PATH = "data/processed/memory_profile.json"
PAIRING_CONFIG_PATH = "data/processed/pairing_config.json"

SCHEMA_FIELDS = ["pair_id", "task_type", "vector_base64", "norm_status"]

def verify_memory_profile():
    """Verify memory_profile.json exists and contains expected structure."""
    logger.info(f"Checking for memory profile at: {MEMORY_JSON_PATH}")
    if not os.path.exists(MEMORY_JSON_PATH):
        logger.error(f"FAIL: {MEMORY_JSON_PATH} does not exist.")
        return False

    try:
        with open(MEMORY_JSON_PATH, 'r') as f:
            data = json.load(f)
        
        # Check required keys based on T008b requirements
        required_keys = ['peak_rss_mb', 'timestamp', 'status']
        for key in required_keys:
            if key not in data:
                logger.error(f"FAIL: {MEMORY_JSON_PATH} missing required key: {key}")
                return False
        
        if not isinstance(data['peak_rss_mb'], (int, float)):
            logger.error(f"FAIL: 'peak_rss_mb' is not a number in {MEMORY_JSON_PATH}")
            return False

        logger.info(f"PASS: Memory profile valid. Peak RSS: {data['peak_rss_mb']} MB")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"FAIL: Invalid JSON in {MEMORY_JSON_PATH}: {e}")
        return False
    except Exception as e:
        logger.error(f"FAIL: Error reading {MEMORY_JSON_PATH}: {e}")
        return False

def verify_baseline_csv():
    """Verify baseline_vectors.csv exists and matches schema."""
    logger.info(f"Checking for baseline vectors at: {BASELINE_CSV_PATH}")
    if not os.path.exists(BASELINE_CSV_PATH):
        logger.error(f"FAIL: {BASELINE_CSV_PATH} does not exist.")
        return False

    try:
        with open(BASELINE_CSV_PATH, 'r', newline='') as f:
            reader = csv.DictReader(f)
            
            # Check headers
            if reader.fieldnames is None:
                logger.error("FAIL: CSV is empty or has no headers.")
                return False
            
            missing_fields = set(SCHEMA_FIELDS) - set(reader.fieldnames)
            if missing_fields:
                logger.error(f"FAIL: CSV missing schema fields: {missing_fields}")
                return False
            
            row_count = 0
            for row in reader:
                row_count += 1
                # Basic validation of vector_base64 (non-empty)
                if not row['vector_base64']:
                    logger.error(f"FAIL: Row {row_count} has empty vector_base64")
                    return False
                # Validate norm_status is boolean-like string
                if row['norm_status'] not in ['True', 'False', 'true', 'false']:
                    logger.warning(f"WARNING: Row {row_count} has unexpected norm_status: {row['norm_status']}")
            
            if row_count == 0:
                logger.error("FAIL: CSV contains no data rows.")
                return False

            logger.info(f"PASS: Baseline CSV valid. Rows: {row_count}")
            return True
    except Exception as e:
        logger.error(f"FAIL: Error reading {BASELINE_CSV_PATH}: {e}")
        return False

def verify_pairing_config():
    """Verify pairing_config.json exists."""
    logger.info(f"Checking for pairing config at: {PAIRING_CONFIG_PATH}")
    if not os.path.exists(PAIRING_CONFIG_PATH):
        logger.error(f"FAIL: {PAIRING_CONFIG_PATH} does not exist.")
        return False
    
    try:
        with open(PAIRING_CONFIG_PATH, 'r') as f:
            data = json.load(f)
        logger.info("PASS: Pairing config exists and is valid JSON.")
        return True
    except Exception as e:
        logger.error(f"FAIL: Error reading {PAIRING_CONFIG_PATH}: {e}")
        return False

def main():
    """Run all verifications."""
    logger.info("Starting T022 Verification: Baseline Extraction & Logging")
    
    results = {
        "memory_profile": verify_memory_profile(),
        "baseline_csv": verify_baseline_csv(),
        "pairing_config": verify_pairing_config()
    }
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("SUCCESS: All T022 verification checks passed.")
        print("T022 Verification: PASSED")
        sys.exit(0)
    else:
        logger.error("FAILURE: One or more T022 verification checks failed.")
        print(f"T022 Verification: FAILED - {results}")
        sys.exit(1)

if __name__ == "__main__":
    main()