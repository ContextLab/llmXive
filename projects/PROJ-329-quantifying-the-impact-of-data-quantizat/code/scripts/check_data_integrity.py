"""
Script to check data integrity for raw and processed directories.
Usage: python scripts/check_data_integrity.py [raw|processed|all]
"""
import argparse
import logging
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_hygiene import (
    get_data_directories,
    verify_data_integrity,
    record_directory_state
)

def main():
    parser = argparse.ArgumentParser(description="Check or update data integrity checksums.")
    parser.add_argument('target', nargs='?', default='all', 
                        choices=['raw', 'processed', 'results', 'all'],
                        help="Which directory to check/update (default: all)")
    parser.add_argument('--action', choices=['verify', 'record'], default='verify',
                        help="Action to perform: verify checksums or record new state")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Determine directories
    dirs_to_process = []
    if args.target == 'all':
        dirs_to_process = get_data_directories()
    else:
        # Map target to specific directory logic if needed, 
        # but get_data_directories returns Path objects. 
        # We filter based on name.
        all_dirs = get_data_directories()
        for d in all_dirs:
            if d.name == args.target:
                dirs_to_process.append(d)
                break
    
    if not dirs_to_process:
        logging.error(f"No directories found for target '{args.target}'")
        sys.exit(1)
    
    for directory in dirs_to_process:
        logging.info(f"Processing {directory.name} ({args.action})...")
        
        if args.action == 'verify':
            is_valid, current, expected = verify_data_integrity(directory)
            if is_valid:
                logging.info(f"  [OK] {directory.name} integrity verified.")
            else:
                logging.error(f"  [FAIL] {directory.name} integrity check failed.")
                if not expected:
                    logging.error("  No previous state found. Run with --action record to initialize.")
        elif args.action == 'record':
            success = record_directory_state(directory)
            if success:
                logging.info(f"  [OK] State recorded for {directory.name}")
            else:
                logging.error(f"  [FAIL] Failed to record state for {directory.name}")

if __name__ == '__main__':
    main()