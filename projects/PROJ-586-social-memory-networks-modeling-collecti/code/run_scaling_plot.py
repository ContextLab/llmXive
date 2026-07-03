"""Entry point for generating the scaling plot.

This script is a thin wrapper that calls the scaling plot generator
with default arguments suitable for the project's US-3 requirements.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analysis.scaling_plot_generator import main

if __name__ == '__main__':
    # Default to project results directory
    results_dir = project_root / 'results'
    output_file = project_root / 'results' / 'scaling_plot.pdf'

    # Override with command-line arguments if provided
    import sys
    if len(sys.argv) == 1:
        sys.argv = [sys.argv[0], '--results-dir', str(results_dir), '--output', str(output_file)]

    sys.exit(main())
