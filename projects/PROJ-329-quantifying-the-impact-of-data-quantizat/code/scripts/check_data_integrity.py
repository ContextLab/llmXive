"""
Script to check data integrity for raw and processed directories.

Usage:
    python scripts/check_data_integrity.py
"""
import argparse
import logging
from pathlib import Path
import sys
from src.data_hygiene import (
    get_data_directories,
    verify_data_integrity
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description='Check data integrity for raw and processed directories.'
    )
    parser.add_argument(
        '--dirs',
        nargs='+',
        choices=['raw', 'processed', 'results', 'all'],
        default=['all'],
        help='Directories to check (default: all)'
    )
    parser.add_argument(
        '--state-file',
        type=Path,
        default=None,
        help='Path to state.yaml (default: auto-detect)'
    )
    
    args = parser.parse_args()
    
    # Determine project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    data_dirs = get_data_directories()
    
    # Determine which directories to check
    if 'all' in args.dirs:
        dirs_to_check = list(data_dirs.items())
    else:
        dirs_to_check = [(d, data_dirs[d]) for d in args.dirs if d in data_dirs]
    
    if not dirs_to_check:
        logger.error("No valid directories specified.")
        sys.exit(1)
    
    logger.info(f"Checking integrity for {len(dirs_to_check)} directories...")
    
    all_valid = True
    
    for dir_name, dir_path in dirs_to_check:
        logger.info(f"Checking {dir_name} directory: {dir_path}")
        
        if not dir_path.exists():
            logger.warning(f"Directory does not exist: {dir_path}")
            all_valid = False
            continue
        
        is_valid, details = verify_data_integrity(dir_path, args.state_file)
        
        if is_valid:
            logger.info(f"  ✓ {dir_name} integrity PASSED")
        else:
            logger.error(f"  ✗ {dir_name} integrity FAILED")
            all_valid = False
            if "missing" in details and details["missing"]:
                logger.error(f"    Missing files: {details['missing']}")
            if "modified" in details and details["modified"]:
                logger.error(f"    Modified files: {details['modified']}")
            if "error" in details:
                logger.error(f"    Error: {details['error']}")
    
    if all_valid:
        logger.info("All checks passed.")
        sys.exit(0)
    else:
        logger.error("Some checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()