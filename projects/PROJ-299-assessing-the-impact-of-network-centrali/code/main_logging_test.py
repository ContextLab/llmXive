"""
Test script to verify logging infrastructure (T005).

This script:
1. Initializes the logging infrastructure.
2. Writes test log entries.
3. Verifies the log file exists and contains valid JSON lines.
"""
import json
import os
from pathlib import Path
from code.utils.logging_config import setup_logging, get_logger, log_event

def main():
    # Initialize logging
    print("Initializing logging infrastructure...")
    logger = setup_logging(level=10, console_output=True)
    test_logger = get_logger("test.T005")

    # Log various test events
    log_event(test_logger, 10, "Debug message test", {"test_id": "T005-01"})
    log_event(test_logger, 20, "Info message test", {"test_id": "T005-02", "status": "ok"})
    log_event(test_logger, 30, "Warning message test", {"test_id": "T005-03", "warning": "low_memory"})
    log_event(test_logger, 40, "Error message test", {"test_id": "T005-04", "error_code": 500})
    
    # Simulate an exception log
    try:
        raise ValueError("Simulated error for T005")
    except Exception:
        test_logger.exception("Exception occurred during test")

    print("Logging complete. Verifying output...")

    log_path = Path("logs/pipeline.log")
    
    if not log_path.exists():
        print("ERROR: Log file was not created at logs/pipeline.log")
        return 1

    # Verify content
    valid_json_count = 0
    line_count = 0
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            line_count += 1
            try:
                data = json.loads(line)
                # Check required fields per FR-011
                assert "timestamp" in data, "Missing timestamp"
                assert "level" in data, "Missing level"
                assert "message" in data, "Missing message"
                valid_json_count += 1
            except json.JSONDecodeError as e:
                print(f"ERROR: Invalid JSON on line {line_count}: {e}")
                return 1
            except AssertionError as e:
                print(f"ERROR: Missing required field on line {line_count}: {e}")
                return 1

    print(f"SUCCESS: Verified {valid_json_count} valid JSON log entries.")
    return 0

if __name__ == "__main__":
    exit(main())
