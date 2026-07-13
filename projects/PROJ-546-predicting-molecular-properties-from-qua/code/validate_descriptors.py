"""
Script to validate the output of generate_descriptors.py.

This script reads the generated CSV file and validates:
1. Required columns are present
2. Physical ranges are reasonable (HOMO < LUMO, charge sum)
3. Data types are correct
"""
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.validation_utils import validate_full, ValidationError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description='Validate molecular descriptor output CSV'
    )
    parser.add_argument(
        'filepath',
        type=Path,
        help='Path to the CSV file to validate (e.g., data/descriptors_semi.csv)'
    )
    
    args = parser.parse_args()
    
    if not args.filepath.exists():
        logger.error(f"File not found: {args.filepath}")
        sys.exit(1)
    
    try:
        if validate_full(args.filepath):
            logger.info(f"Validation PASSED for {args.filepath}")
            sys.exit(0)
    except ValidationError as e:
        logger.error(f"Validation FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
