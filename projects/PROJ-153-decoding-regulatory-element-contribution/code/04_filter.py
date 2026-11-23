"""
T054: Final Data Integrity Assertion
Verifies that zero synthetic or mock data sources were loaded during the pipeline execution.
Scans logs/pipeline.log for forbidden keywords and aborts if found.
"""
import os
import sys
import re
import logging
import argparse
from pathlib import Path

# Configure logging to match project standards (ISO8601, level, message)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Forbidden keywords to search for in the log (case-insensitive)
# Matches: synthetic, mock, fallback, placeholder
FORBIDDEN_PATTERN = re.compile(r'(?i)(synthetic|mock|fallback|placeholder)')

def scan_log_for_synthetic_data(log_path: Path) -> list:
    """
    Scans the specified log file for forbidden keywords indicating synthetic/mock data usage.
    
    Args:
        log_path (Path): Path to the pipeline log file.
        
    Returns:
        list: A list of tuples (line_number, line_content) where forbidden keywords were found.
    """
    violations = []
    
    if not log_path.exists():
        logger.error(f"Log file not found: {log_path}")
        # If the log file doesn't exist, we cannot verify integrity. 
        # However, per FR-001, we must fail loudly if we can't verify.
        # But strictly, the task is to check for *synthetic* data. 
        # If no log exists, we assume no synthetic data was logged, but this is a warning state.
        # Given the strict "abort if any are found", and the inability to check, 
        # we should probably fail if the log is missing in a strict mode, 
        # but the primary task is checking the content. 
        # Let's return empty if missing but log a critical warning, 
        # or fail if the pipeline expects the log to exist.
        # Given T037 creates logs, if this script runs, logs should exist.
        # We will treat missing log as a failure to verify integrity.
        raise FileNotFoundError(f"Integrity check failed: Log file {log_path} does not exist. Cannot verify data source integrity.")

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, 1):
                if FORBIDDEN_PATTERN.search(line):
                    violations.append((line_number, line.strip()))
    except Exception as e:
        logger.error(f"Error reading log file {log_path}: {e}")
        raise

    return violations

def main():
    parser = argparse.ArgumentParser(description='Verify no synthetic/mock data was used in pipeline execution.')
    parser.add_argument('--log-path', type=str, default='logs/pipeline.log',
                        help='Path to the pipeline log file (default: logs/pipeline.log)')
    parser.add_argument('--exit-on-violation', action='store_true', default=True,
                        help='Exit with code 1 if violations are found (default: True)')
    
    args = parser.parse_args()
    
    log_path = Path(args.log_path)
    
    logger.info(f"Starting data integrity assertion scan on: {log_path}")
    
    try:
        violations = scan_log_for_synthetic_data(log_path)
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    if violations:
        logger.error("CRITICAL: Synthetic or mock data sources detected in pipeline logs!")
        logger.error(f"Found {len(violations)} violation(s):")
        for line_num, content in violations:
            logger.error(f"  Line {line_num}: {content}")
        
        if args.exit_on_violation:
            logger.error("ABORTING pipeline execution due to data integrity violation.")
            sys.exit(1)
        else:
            logger.warning("Continuing despite violations (exit-on-violation disabled).")
    else:
        logger.info("SUCCESS: No synthetic, mock, fallback, or placeholder data sources detected.")
        logger.info("Data integrity assertion passed.")
        sys.exit(0)

if __name__ == '__main__':
    main()