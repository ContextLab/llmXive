"""
Crystallographic descriptor calculation module.

This module computes structural descriptors including octahedral tilting
angles, bond-length variance, tolerance factors, and unit cell volumes
with deterministic seed support for reproducibility.
"""

import argparse
from pathlib import Path

from src.utils.seed import set_seed, get_seed_parser

__version__ = '0.1.0'
__all__ = ['compute_descriptors', 'set_seed', 'get_seed_parser']

# Import submodules to expose their functionality
try:
    from .compute_descriptors import compute_descriptors
except ImportError:
    def compute_descriptors(df=None, seed: int = 42):
        """Placeholder - actual implementation in compute_descriptors.py"""
        set_seed(seed)
        raise NotImplementedError("compute_descriptors.py not yet implemented")

def main():
    """Main entry point for descriptor calculation with seed support."""
    parser = argparse.ArgumentParser(
        description='Descriptor calculation pipeline with deterministic seed support'
    )
    parser = get_seed_parser(parser)
    parser.add_argument(
        '--input-path',
        type=str,
        default='data/cleaned/merged_perovskites.csv',
        help='Path to cleaned input data'
    )
    parser.add_argument(
        '--output-path',
        type=str,
        default='data/results/descriptors.csv',
        help='Output path for computed descriptors'
    )
    
    args = parser.parse_args()
    
    # Set seed for reproducibility
    set_seed(args.seed)
    
    print(f"Initialized descriptor pipeline with seed={args.seed}")
    print(f"Input path: {args.input_path}")
    print(f"Output path: {args.output_path}")
    
    return args

if __name__ == '__main__':
    main()
