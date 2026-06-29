"""
Data ingestion module for Materials Project API and literature sources.

This module handles downloading crystal structures and thermal conductivity
data with deterministic seed support for reproducibility.
"""

import argparse
from pathlib import Path

from src.utils.seed import set_seed, get_seed_parser

__version__ = '0.1.0'
__all__ = ['fetch_structures', 'fetch_thermal', 'set_seed', 'get_seed_parser']

# Import submodules to expose their functionality
try:
    from .fetch_structures import fetch_structures
except ImportError:
    def fetch_structures(api_key: str = None, seed: int = 42):
        """Placeholder - actual implementation in fetch_structures.py"""
        set_seed(seed)
        raise NotImplementedError("fetch_structures.py not yet implemented")

try:
    from .fetch_thermal import fetch_thermal
except ImportError:
    def fetch_thermal(csv_paths: list = None, seed: int = 42):
        """Placeholder - actual implementation in fetch_thermal.py"""
        set_seed(seed)
        raise NotImplementedError("fetch_thermal.py not yet implemented")

def main():
    """Main entry point for ingestion pipeline with seed support."""
    parser = argparse.ArgumentParser(
        description='Data ingestion pipeline with deterministic seed support'
    )
    parser = get_seed_parser(parser)
    parser.add_argument(
        '--materials-project-key',
        type=str,
        help='Materials Project API key (or set MP_API_KEY env var)'
    )
    parser.add_argument(
        '--thermal-data-path',
        type=str,
        help='Path to thermal conductivity CSV files'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/raw',
        help='Output directory for downloaded data'
    )
    
    args = parser.parse_args()
    
    # Set seed for reproducibility
    set_seed(args.seed)
    
    print(f"Initialized ingestion pipeline with seed={args.seed}")
    print(f"Output directory: {args.output_dir}")
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    return args

if __name__ == '__main__':
    main()
