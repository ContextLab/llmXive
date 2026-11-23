"""
Initialization script to ensure data/run_log.json exists as an empty array.
This script is executed to satisfy T005 verification requirements.
"""
import os
import json
from pathlib import Path

def main():
    log_path = Path("data/run_log.json")
    if not log_path.exists():
        os.makedirs(log_path.parent, exist_ok=True)
        with open(log_path, 'w') as f:
            json.dump([], f)
        print(f"Created empty log file: {log_path}")
    else:
        print(f"Log file already exists: {log_path}")
    
    # Verify content is an empty array
    with open(log_path, 'r') as f:
        content = json.load(f)
    assert content == [], "Log file must be an empty array []"
    print("Verification passed: data/run_log.json is an empty JSON array.")

if __name__ == "__main__":
    main()
