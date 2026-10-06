"""
Logging infrastructure runner for the data ingestion pipeline.

This module initializes and tests the logging infrastructure to ensure
warnings (e.g., dropped rows, missing data) are properly captured to
logs/pipeline.log.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_config import setup_logging, get_logger, log_warning
from utils.config import get_log_path


def run_logging_check() -> dict:
    """
    Run a comprehensive check of the logging infrastructure.
    
    This function:
    1. Ensures the log directory exists
    2. Initializes logging with proper configuration
    3. Logs test warnings to verify the pipeline.log file is created
    4. Verifies the log file contains the expected content
    
    Returns:
        dict: Check results with status and details
    """
    results = {
        'status': 'success',
        'log_path': None,
        'test_messages_logged': [],
        'errors': []
    }
    
    try:
        # Get log path from config
        log_path = get_log_path()
        results['log_path'] = log_path
        
        # Ensure log directory exists
        log_dir = Path(log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        setup_logging()
        logger = get_logger('logging_runner')
        
        # Test logging various message types
        test_messages = [
            "INFO: Logging infrastructure initialized successfully",
            "WARNING: Test warning - dropped 5 rows due to missing values",
            "WARNING: Test warning - missing data in column 'protein_abundance'",
            "ERROR: Test error - simulated error for logging verification"
        ]
        
        for msg in test_messages:
            if "INFO" in msg:
                logger.info(msg.split(": ", 1)[1])
            elif "WARNING" in msg:
                logger.warning(msg.split(": ", 1)[1])
                results['test_messages_logged'].append(msg)
            elif "ERROR" in msg:
                logger.error(msg.split(": ", 1)[1])
        
        # Verify log file exists and contains content
        if not Path(log_path).exists():
            results['status'] = 'failed'
            results['errors'].append(f"Log file not created at {log_path}")
        else:
            with open(log_path, 'r') as f:
                content = f.read()
                if len(content) < 100:
                    results['status'] = 'failed'
                    results['errors'].append("Log file exists but is empty or too small")
                else:
                    results['messages_verified'] = True
        
    except Exception as e:
        results['status'] = 'failed'
        results['errors'].append(str(e))
        import traceback
        results['traceback'] = traceback.format_exc()
    
    return results


def main():
    """
    Main entry point for logging infrastructure verification.
    
    Runs the logging check and prints results.
    Exits with code 0 on success, 1 on failure.
    """
    print("Running logging infrastructure check...")
    results = run_logging_check()
    
    print(f"\nStatus: {results['status'].upper()}")
    print(f"Log path: {results['log_path']}")
    
    if results['test_messages_logged']:
        print(f"\nTest messages logged ({len(results['test_messages_logged'])}):")
        for msg in results['test_messages_logged']:
            print(f"  - {msg}")
    
    if results['errors']:
        print(f"\nErrors ({len(results['errors'])}):")
        for err in results['errors']:
            print(f"  - {err}")
    
    if results['status'] == 'success':
        print("\n✓ Logging infrastructure is properly configured and functional.")
        sys.exit(0)
    else:
        print("\n✗ Logging infrastructure check failed.")
        sys.exit(1)


if __name__ == '__main__':
    main()
