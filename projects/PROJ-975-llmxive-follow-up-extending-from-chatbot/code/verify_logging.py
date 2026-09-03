import os
import sys
import csv
import json
from code.logging_config import get_logger, log_experiment_entry, verify_log_file_exists, LOG_COLUMNS

def main():
    """
    Verification script for T007.
    Writes a test entry and confirms file existence and schema compliance.
    """
    print("Starting T007 verification...")
    
    # 1. Initialize logger and write a test entry
    logger = get_logger()
    test_entry = {
        "task_id": "T007-VERIFY",
        "skill_id": "S-VERIFY",
        "success": True,
        "latency": 1.23,
        "tokens": 256,
        "retrieval_precision": 0.95,
        "retrieval_diversity": 0.15,
        "pruning_risk_count": 0,
        "library_size": 10,
        "pruning_enabled": True,
        "edge_case": False
    }
    
    log_experiment_entry(test_entry)
    
    # 2. Verify file existence
    if not verify_log_file_exists():
        print("FAIL: Log file does not exist or is empty.")
        sys.exit(1)
    
    print("PASS: Log file exists and is not empty.")
    
    # 3. Verify schema compliance
    log_path = os.path.join("data", "results", "experiment_log.csv")
    try:
        with open(log_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                print("FAIL: CSV file has no headers.")
                sys.exit(1)
            
            # Check if all expected columns are present
            missing = set(LOG_COLUMNS) - set(headers)
            if missing:
                print(f"FAIL: Missing columns in CSV: {missing}")
                sys.exit(1)
            
            # Read the written row
            rows = list(reader)
            if not rows:
                print("FAIL: No data rows found.")
                sys.exit(1)
            
            last_row = rows[-1]
            if last_row['task_id'] != 'T007-VERIFY':
                print(f"FAIL: Task ID mismatch. Expected 'T007-VERIFY', got '{last_row['task_id']}'")
                sys.exit(1)
            
            print("PASS: Schema compliance verified.")
            print(f"Headers: {headers}")
            print(f"Sample row: {last_row}")
            
    except FileNotFoundError:
        print("FAIL: Log file not found during verification.")
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: Error during verification: {e}")
        sys.exit(1)
        
    print("T007 Verification Complete: SUCCESS")

if __name__ == "__main__":
    main()