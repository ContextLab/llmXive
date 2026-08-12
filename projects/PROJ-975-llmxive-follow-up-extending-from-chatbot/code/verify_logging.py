"""
verify_logging.py

Verification script for T007.
Runs a test that writes a log entry and confirms file existence and schema compliance.
"""
import os
import sys
import csv
import json

# Add project root to path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.logging_config import get_logger, log_experiment_entry, verify_log_file_exists

def main():
    print("Starting T007 verification...")
    
    # 1. Verify file existence (initially might not exist)
    exists_before = verify_log_file_exists()
    print(f"Log file exists before run: {exists_before}")
    
    # 2. Write a test entry
    print("Writing test experiment entry...")
    log_experiment_entry(
        task_id="test_task_001",
        success=True,
        latency=0.123,
        tokens=50,
        retrieval_precision=0.85,
        retrieval_diversity=0.45,
        pruning_risk_count=0,
        library_size=100,
        pruning_enabled=False
    )
    
    # 3. Verify file existence after write
    exists_after = verify_log_file_exists()
    if not exists_after:
        print("ERROR: Log file was not created.")
        return False
    print("Log file created successfully.")
    
    # 4. Verify schema compliance (column structure)
    schema_path = "contracts/experiment_log.schema.yaml"
    expected_columns = None
    
    if os.path.exists(schema_path):
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        expected_columns = list(schema.get('properties', {}).keys())
        print(f"Expected columns from schema: {expected_columns}")
    else:
        print("Schema file not found. Skipping column verification.")
        
    # Read the CSV and check headers
    log_path = "data/results/experiment_log.csv"
    with open(log_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        print(f"Actual headers in CSV: {headers}")
        
        if expected_columns:
            if set(headers) != set(expected_columns):
                print(f"ERROR: Column mismatch. Expected {expected_columns}, got {headers}")
                return False
            print("Column structure matches schema.")
    
    # 5. Verify data content
    with open(log_path, 'r') as f:
        reader = csv.DictReader(f)
        row = next(reader)
        
        assert row['task_id'] == 'test_task_001', "task_id mismatch"
        assert row['success'] == 'true', "success mismatch"
        assert row['latency'] == '0.123', "latency mismatch"
        assert row['library_size'] == '100', "library_size mismatch"
        
    print("Verification PASSED: Log file exists, schema compliant, and data correct.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
