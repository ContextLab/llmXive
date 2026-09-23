import argparse
import logging
import sys
import re
from pathlib import Path
from typing import Dict, Any, Optional

from src.utils.logger import get_logger

def validate_exclusion_log(log_path: str, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Validates the existence and content of the covariate exclusion log file.
    
    Args:
        log_path: Path to the covariate_exclusion_log.txt file.
        logger: Optional logger instance. If None, a default logger is created.
    
    Returns:
        A dictionary containing validation results:
            - 'exists': bool, whether the file exists
            - 'valid': bool, whether the file contains valid counts
            - 'counts': dict, parsed counts if valid, empty dict otherwise
            - 'error': str, error message if any validation step fails
    """
    if logger is None:
        logger = get_logger(__name__)
    
    result = {
        'exists': False,
        'valid': False,
        'counts': {},
        'error': None
    }
    
    log_file = Path(log_path)
    
    # Check if file exists
    if not log_file.exists():
        result['error'] = f"File not found: {log_path}"
        logger.error(result['error'])
        return result
    
    result['exists'] = True
    logger.info(f"File exists: {log_path}")
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
    
        if not content:
            result['error'] = "File is empty"
            logger.error(result['error'])
            return result
    
        # Parse the log content
        # Expected format: "Excluded X samples due to >20% missing covariate data."
        # or similar patterns containing the count
        pattern = r'Excluded\s+(\d+)\s+samples?\s+due\s+to\s+.*missing.*covariate.*data\.?'
        match = re.search(pattern, content, re.IGNORECASE)
        
        if not match:
            # Try a more general pattern for any numeric count
            general_pattern = r'(\d+)\s+samples?\s+excluded'
            match = re.search(general_pattern, content, re.IGNORECASE)
        
        if match:
            excluded_count = int(match.group(1))
            result['counts'] = {'excluded_samples': excluded_count}
            result['valid'] = True
            logger.info(f"Validation successful. Found {excluded_count} excluded samples.")
        else:
            result['error'] = "Could not parse excluded sample count from log file"
            logger.error(result['error'])
            logger.info(f"File content:\n{content}")
            
    except Exception as e:
        result['error'] = f"Error reading or parsing log file: {str(e)}"
        logger.error(result['error'])
    
    return result

def build_arg_parser() -> argparse.ArgumentParser:
    """Build command line argument parser for the validation script."""
    parser = argparse.ArgumentParser(
        description="Validate the covariate exclusion log file."
    )
    parser.add_argument(
        "--log-path",
        type=str,
        default="data/processed/results/covariate_exclusion_log.txt",
        help="Path to the covariate exclusion log file to validate."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )
    return parser

def main():
    """Main entry point for the validation script."""
    parser = build_arg_parser()
    args = parser.parse_args()
    
    # Configure logging
    logger = get_logger(__name__, level=logging.DEBUG if args.verbose else logging.INFO)
    
    logger.info(f"Validating exclusion log at: {args.log_path}")
    
    validation_result = validate_exclusion_log(args.log_path, logger)
    
    if validation_result['valid']:
        logger.info("VALIDATION PASSED: Exclusion log is valid.")
        logger.info(f"Excluded samples: {validation_result['counts'].get('excluded_samples', 'N/A')}")
        sys.exit(0)
    else:
        logger.error("VALIDATION FAILED")
        if validation_result['error']:
            logger.error(f"Reason: {validation_result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
