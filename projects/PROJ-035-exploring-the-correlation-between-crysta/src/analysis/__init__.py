"""
Statistical analysis module for correlation and regression modeling.

This module performs stratified correlation analysis, multiple linear
regression with cross-validation, and sensitivity analysis with
deterministic seed support for reproducibility.
"""

import argparse
from pathlib import Path

from src.utils.seed import set_seed, get_seed_parser

__version__ = '0.1.0'
__all__ = [
    'stratify', 'correlation', 'sensitivity', 'regression',
    'visualize', 'set_seed', 'get_seed_parser'
]

# Import submodules to expose their functionality
try:
    from .stratify import stratify
except ImportError:
    def stratify(df=None, seed: int = 42):
        """Placeholder - actual implementation in stratify.py"""
        set_seed(seed)
        raise NotImplementedError("stratify.py not yet implemented")

try:
    from .correlation import correlation
except ImportError:
    def correlation(df=None, seed: int = 42):
        """Placeholder - actual implementation in correlation.py"""
        set_seed(seed)
        raise NotImplementedError("correlation.py not yet implemented")

try:
    from .sensitivity import sensitivity
except ImportError:
    def sensitivity(df=None, seed: int = 42):
        """Placeholder - actual implementation in sensitivity.py"""
        set_seed(seed)
        raise NotImplementedError("sensitivity.py not yet implemented")

try:
    from .regression import regression
except ImportError:
    def regression(df=None, seed: int = 42):
        """Placeholder - actual implementation in regression.py"""
        set_seed(seed)
        raise NotImplementedError("regression.py not yet implemented")

try:
    from .visualize import visualize
except ImportError:
    def visualize(df=None, seed: int = 42):
        """Placeholder - actual implementation in visualize.py"""
        set_seed(seed)
        raise NotImplementedError("visualize.py not yet implemented")

def main():
    """Main entry point for analysis pipeline with seed support."""
    parser = argparse.ArgumentParser(
        description='Statistical analysis pipeline with deterministic seed support'
    )
    parser = get_seed_parser(parser)
    parser.add_argument(
        '--input-path',
        type=str,
        default='data/results/descriptors.csv',
        help='Path to input data with descriptors'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/results',
        help='Output directory for analysis results'
    )
    parser.add_argument(
        '--figures-dir',
        type=str,
        default='figures',
        help='Output directory for generated figures'
    )
    
    args = parser.parse_args()
    
    # Set seed for reproducibility
    set_seed(args.seed)
    
    print(f"Initialized analysis pipeline with seed={args.seed}")
    print(f"Input path: {args.input_path}")
    print(f"Output directory: {args.output_dir}")
    print(f"Figures directory: {args.figures_dir}")
    
    return args

if __name__ == '__main__':
    main()
