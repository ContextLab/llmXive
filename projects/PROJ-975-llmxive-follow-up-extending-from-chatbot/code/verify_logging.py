"""
verify_logging.py

Verification script for T007:
Runs a test script that writes a log entry and confirms file existence.
"""
import os
import sys
import json
from code.logging_config import get_logger, log_experiment_entry, verify_log_file_exists

def main():
    """
    Executes the verification logic for T007.
    1. Writes a log entry using the configured logger.
    2. Confirms the file exists.
    3. Prints success or failure.
    """
    print("Starting verification for T007 (logging_config)...")
    
    try:
        # 1. Write a log entry
        logger = get_logger("verification_test")
        logger.info("Verification test: Writing a log entry to experiment_log.csv")
        
        # Also test the structured entry function
        log_experiment_entry(
            task_id="T007-verify",
            success=True,
            latency=0.001,
            tokens=0,
            retrieval_precision=0.0,
            retrieval_diversity=0.0,
            pruning_risk_count=0,
            library_size=10,
            pruning_enabled=False,
            extra_metadata={"verification": True}
        )
        
        print("Log entries written successfully.")
        
        # 2. Confirm file existence
        if verify_log_file_exists():
            print("SUCCESS: data/results/experiment_log.csv exists.")
            
            # Optional: Print the last few lines to show content
            from code.logging_config import LOG_FILE_PATH
            with open(LOG_FILE_PATH, 'r') as f:
                lines = f.readlines()
                print(f"Total lines in log file: {len(lines)}")
                if len(lines) > 1:
                    print("Last log entry metadata:")
                    import csv
                    reader = csv.DictReader(lines)
                    last_row = None
                    for row in reader:
                        last_row = row
                    if last_row and last_row.get("metadata_json"):
                        print(json.dumps(json.loads(last_row["metadata_json"]), indent=2))
            
            return 0
        else:
            print("FAILURE: data/results/experiment_log.csv does not exist.")
            return 1
            
    except Exception as e:
        print(f"ERROR during verification: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())