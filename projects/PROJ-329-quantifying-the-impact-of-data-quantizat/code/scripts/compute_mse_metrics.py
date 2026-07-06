"""
Script to compute MSE metrics for T023.
Wraps the analysis module to compute MSE between injected ground-truth 
and recovered posterior means for chirp mass, spin, and distance.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'code'))

from src.analysis import main

def run():
    """Run the MSE computation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Default paths
    results_file = project_root / 'data' / 'results' / 'inference_pilot_42.json'
    mse_output = project_root / 'data' / 'results' / 'mse_metrics_pilot_42.json'
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        results_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        mse_output = Path(sys.argv[2])
    
    if not results_file.exists():
        logging.error(f"Results file not found: {results_file}")
        logging.error("Please ensure inference results exist before running this script.")
        return 1
    
    # Set command line arguments for the analysis module
    sys.argv = [
        'compute_mse_metrics.py',
        '--input', str(results_file),
        '--output', str(mse_output)
    ]
    
    return main()

if __name__ == '__main__':
    sys.exit(run())
