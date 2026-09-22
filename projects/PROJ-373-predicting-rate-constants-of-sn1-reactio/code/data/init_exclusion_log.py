import os
import sys
import logging
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs, DataConfig
from utils.logger import get_logger

logger = get_logger(__name__)

def initialize_exclusion_log(file_path: str):
    """Initialize exclusion log file with headers."""
    with open(file_path, 'w') as f:
        f.write('row_index,reason,original_smiles\n')
    logger.info(f"Exclusion log initialized: {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Initialize exclusion log")
    parser.add_argument("--output", type=str, default="data/processed/exclusion_raw.log", help="Output file path")
    args = parser.parse_args()

    ensure_dirs()
    
    try:
        initialize_exclusion_log(args.output)
    except Exception as e:
        logger.error(f"Failed to initialize exclusion log: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()