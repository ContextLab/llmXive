"""
Descriptor validation script.

Validates output CSV files from descriptor generation for:
- Required columns presence
- Physical ranges (HOMO < LUMO, charge sum matches net charge)
- Data types
"""

import argparse
import logging
import sys
from pathlib import Path

from utils.validation_utils import validate_full, ValidationError

logger = logging.getLogger(__name__)

def main():
    """Main entry point for descriptor validation."""
    parser = argparse.ArgumentParser(
        description='Validate molecular descriptor CSV files'
    )
    parser.add_argument(
        'filepath',
        type=Path,
        help='Path to the descriptor CSV file to validate'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=None,
        help='Path to write validation report (optional)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed error messages'
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    if not args.filepath.exists():
        logger.error(f"File not found: {args.filepath}")
        sys.exit(1)
    
    try:
        logger.info(f"Validating {args.filepath}...")
        is_valid, errors = validate_full(args.filepath)
        
        if is_valid:
            logger.info(f"✓ Validation passed: {args.filepath}")
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(f"Validation passed for {args.filepath}\n")
            sys.exit(0)
        else:
            logger.error(f"✗ Validation failed: {args.filepath}")
            logger.error(f"Found {len(errors)} error(s):")
            for i, error in enumerate(errors, 1):
                logger.error(f"  {i}. {error}")
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(f"Validation failed for {args.filepath}\n")
                    f.write(f"Found {len(errors)} error(s):\n")
                    for error in errors:
                        f.write(f"  - {error}\n")
            
            sys.exit(1)
            
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(3)

if __name__ == '__main__':
    main()