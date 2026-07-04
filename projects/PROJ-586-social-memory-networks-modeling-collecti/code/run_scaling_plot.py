"""
Wrapper script to generate scaling_plot.pdf for T030.

This script orchestrates the scaling plot generation, ensuring the output
file is created at the correct location as specified in tasks.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analysis.scaling_plot_generator import main as plot_main


def main() -> int:
    """Main entry point."""
    # Default paths as per tasks.md
    data_path = code_dir / 'data' / 'scaling_results.csv'
    output_path = code_dir.parent / 'results' / 'scaling_plot.pdf'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run the plot generation with explicit paths
    sys.argv = [
        'run_scaling_plot.py',
        '--data', str(data_path),
        '--output', str(output_path),
        '--metric', 'specialization_index'
    ]
    
    return plot_main()


if __name__ == '__main__':
    sys.exit(main())
