"""
Data cleaning and merging module for perovskite datasets.

This module handles merging, validation, and cleaning of crystal structure
and thermal conductivity data with deterministic seed support.
"""

import argparse
from pathlib import Path

from src.utils.seed import set_seed, get_seed_parser

__version__ = '0.1.0'
__all__ = ['clean_merge', 'provenance_validator', 'temperature_normalize', 'set_seed', 'get_seed_parser']

# Import submodules to expose their functionality
try:
    from .clean_merge import clean_merge
except ImportError:
    def clean_merge(structures_df=None, thermal_df=None, seed: int = 42):
        """Placeholder - actual implementation in clean_merge.py"""
        set_seed(seed)
        raise NotImplementedError("clean_merge.py not yet implemented")

try:
    from .provenance_validator import provenance_validator
except ImportError:
    def provenance_validator(df=None, seed: int = 42):
        """Placeholder - actual implementation in provenance_validator.py"""
        set_seed(seed)
        raise NotImplementedError("provenance_validator.py not yet implemented")

try:
    from .temperature_normalize import temperature_normalize
except ImportError:
    def temperature_normalize(df=None, seed: int = 42):
        """Placeholder - actual implementation in temperature_normalize.py"""
        set_seed(seed)
        raise NotImplementedError("temperature_normalize.py not yet implemented")

def main():
    """Main entry point for cleaning pipeline with seed support."""
    parser = argparse.ArgumentParser(
        description='Data cleaning pipeline with deterministic seed support'
    )
    parser = get_seed_parser(parser)
    parser.add_argument(
        '--structures-path',
        type=str,
        help='Path to raw structures CSV'
    )
    parser.add_argument(
        '--thermal-path',
        type=str,
        help='Path to raw thermal conductivity CSV'
    )
    parser.add_argument(
        '--output-path',
        type=str,
        default='data/cleaned/merged_perovskites.csv',
        help='Output path for cleaned merged data'
    )
    
    args = parser.parse_args()
    
    # Set seed for reproducibility
    set_seed(args.seed)
    
    print(f"Initialized cleaning pipeline with seed={args.seed}")
    print(f"Output path: {args.output_path}")
    
    return args

if __name__ == '__main__':
    main()
