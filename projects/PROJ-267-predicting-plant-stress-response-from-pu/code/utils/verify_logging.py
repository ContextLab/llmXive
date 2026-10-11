"""
Verification script for T006 to prove the logger creates the log file
and correctly records the required event types.
"""
import sys
from pathlib import Path
from code.utils.logging_config import get_logger

def main():
    # Initialize logger
    logger = get_logger("verify_logging")
    
    # 1. Simulate dropped rows (INFO)
    logger.info("SIMULATION: Dropped 15 rows due to low abundance filter (< 50% detection).")
    
    # 2. Simulate missing columns (WARN)
    logger.warning("SIMULATION: Missing column 'protein_id' in input CSV; skipping merge.")
    
    # 3. Simulate raised errors (ERROR)
    try:
        raise RuntimeError("SIMULATION: Failed to connect to ProteomeXchange API.")
    except RuntimeError as e:
        logger.error(f"SIMULATION: {e}")

    # Verification of the artifact
    # We use the known canonical path logs/pipeline.log
    log_file = Path("logs/pipeline.log")
    
    if not log_file.exists():
        print("FAIL: logs/pipeline.log was not created.")
        sys.exit(1)
        
    content = log_file.read_text()
    checks = [
        "Dropped 15 rows",
        "Missing column 'protein_id'",
        "Failed to connect to ProteomeXchange API"
    ]
    
    for check in checks:
        if check not in content:
            print(f"FAIL: Log missing expected entry: {check}")
            sys.exit(1)
            
    print("SUCCESS: logs/pipeline.log created and contains all required entries.")
    sys.exit(0)

if __name__ == "__main__":
    main()
