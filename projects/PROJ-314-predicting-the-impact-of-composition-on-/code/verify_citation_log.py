"""
Verification script for T010b: Verify logs/citation_validation.log creation.

This script executes the ingestion module with dummy URLs to trigger
the citation validation logic and verifies that the log file is created
with the expected format.
"""
import os
import sys
import logging
import time
from pathlib import Path
from ingestion import validate_source_citations

def main():
    """
    Execute citation validation with dummy URLs and verify log creation.
    """
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / "citation_validation.log"
    
    # Remove existing log to ensure fresh test
    if log_file.exists():
        log_file.unlink()
    
    # Configure logging to file
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Test with dummy URL
    dummy_urls = ['https://example.com']
    
    print(f"Running citation validation for: {dummy_urls}")
    
    # Call the validation function
    try:
        results = validate_source_citations(dummy_urls)
        print(f"Validation completed. Results: {results}")
    except Exception as e:
        print(f"Validation raised exception: {e}")
    
    # Give logging a moment to flush
    time.sleep(0.5)
    
    # Verify log file exists
    if not log_file.exists():
        print("FAIL: Log file was not created")
        sys.exit(1)
    
    # Read and verify log content
    with open(log_file, 'r') as f:
        content = f.read()
    
    print(f"Log file contents:\n{content}")
    
    # Check for expected format
    if not content:
        print("FAIL: Log file is empty")
        sys.exit(1)
    
    # Verify format: INFO: Citation validation for {url}: {status}
    has_valid_entry = False
    for line in content.split('\n'):
        if line.startswith('INFO: Citation validation for'):
            if ':' in line.split('Citation validation for ')[1]:
                has_valid_entry = True
                break
    
    if not has_valid_entry:
        print("FAIL: No valid log entry found with expected format")
        sys.exit(1)
    
    print("SUCCESS: Log file created with valid entry format")
    sys.exit(0)

if __name__ == "__main__":
    main()
