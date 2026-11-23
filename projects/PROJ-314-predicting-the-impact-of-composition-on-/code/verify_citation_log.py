"""
Verification script for T010b: Verify logs/citation_validation.log creation.

Executes ingestion.py with dummy URLs to trigger citation validation logic
and verifies that the log file is created and populated correctly.
"""
import os
import sys
import logging
import time
from pathlib import Path

# Add parent directory to path to import ingestion module
sys.path.insert(0, str(Path(__file__).parent))

from ingestion import validate_source_citations, setup_citation_logger

def main():
    """
    Main verification routine for T010b.
    
    1. Ensures logs directory exists.
    2. Runs validation on a dummy URL.
    3. Verifies log file creation and content format.
    """
    # Ensure logs directory exists
    logs_dir = Path(__file__).parent.parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup logger to write to the specific file
    log_file = logs_dir / "citation_validation.log"
    setup_citation_logger(log_file_path=str(log_file))
    
    dummy_urls = ['https://example.com']
    
    print(f"Running citation validation for dummy URLs: {dummy_urls}")
    
    # Run the validation logic (this will trigger the logger)
    # Note: validate_source_citations expects a list of dicts with 'url' key
    dummy_sources = [{'url': url, 'title': 'Test Title'} for url in dummy_urls]
    
    try:
        validate_source_citations(dummy_sources)
    except Exception as e:
        # We expect failures for dummy URLs, but the log should still be written
        print(f"Validation expected to fail for dummy URLs: {e}")
    
    # Verify log file exists
    if not log_file.exists():
        print("FAILURE: logs/citation_validation.log was not created.")
        sys.exit(1)
    
    # Verify log content
    content = log_file.read_text()
    if not content:
        print("FAILURE: logs/citation_validation.log is empty.")
        sys.exit(1)
    
    # Check for expected format: INFO: Citation validation for {url}: {status}
    expected_format_found = False
    for line in content.splitlines():
        if "INFO: Citation validation for" in line and ":" in line.split("Citation validation for ")[1]:
            expected_format_found = True
            print(f"SUCCESS: Found valid log entry: {line.strip()}")
            break
    
    if not expected_format_found:
        print("FAILURE: Log file does not contain entries in expected format 'INFO: Citation validation for {url}: {status}'.")
        print("Content found:")
        print(content)
        sys.exit(1)
    
    print("T010b Verification: PASSED")
    print(f"Log file verified: {log_file}")

if __name__ == "__main__":
    main()
