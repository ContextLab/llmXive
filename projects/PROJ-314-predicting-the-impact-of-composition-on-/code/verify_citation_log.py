"""
Verification script for citation validation log (T010b).

This script executes the citation validation logic with dummy URLs
to verify that logs/citation_validation.log is created and populated
with the expected format.

Usage:
    python code/verify_citation_log.py
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion import validate_source_citations
from code import logger

def main():
    """
    Execute citation validation with dummy URLs to verify log creation.
    
    This satisfies T010b:
    1. Runs validate_source_citations() with dummy URLs
    2. Verifies logs/citation_validation.log exists
    3. Verifies log contains entries with format:
       "INFO: Citation validation for {url}: {status}"
    """
    # Define dummy URLs for testing
    # Using example.com and a non-routable IP to trigger failures
    dummy_urls = [
        'https://example.com',
        'http://192.0.2.1'  # TEST-NET-1, will fail to resolve
    ]

    # Ensure logs directory exists
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)

    # Run validation
    logger.info(f"Starting citation validation for {len(dummy_urls)} dummy URLs")
    results = validate_source_citations(dummy_urls)

    # Verify log file exists
    log_file = logs_dir / 'citation_validation.log'
    if not log_file.exists():
        print("ERROR: logs/citation_validation.log was not created")
        sys.exit(1)

    # Verify log content
    with open(log_file, 'r') as f:
        content = f.read()

    # Check for expected log format
    found_valid_entry = False
    for url in dummy_urls:
        if f"Citation validation for {url}:" in content:
            found_valid_entry = True
            break

    if not found_valid_entry:
        print("ERROR: Log file does not contain expected entries")
        print(f"Log content:\n{content}")
        sys.exit(1)

    # Verify at least one status is not empty
    lines = content.split('\n')
    has_non_empty_status = False
    for line in lines:
        if "Citation validation for" in line and "INFO" in line:
            # Extract status part after the last colon
            parts = line.split(':')
            if len(parts) >= 3:
                status = parts[-1].strip()
                if status:  # Status is not empty
                    has_non_empty_status = True
                    break

    if not has_non_empty_status:
        print("ERROR: No log entry found with non-empty status")
        print(f"Log content:\n{content}")
        sys.exit(1)

    print("SUCCESS: Citation validation log verified")
    print(f"  - Log file exists: {log_file}")
    print(f"  - Contains expected format: Yes")
    print(f"  - Contains non-empty status: Yes")
    print(f"  - Validation results: {len(results)} URLs processed")

    return 0

if __name__ == "__main__":
    sys.exit(main())
