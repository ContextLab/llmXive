import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'code'))

from src.analysis import run_analysis, generate_significance_flag, main as analysis_main
from src.robustness import merge_convergence_results, run_sensitivity_sweep, main as robustness_main

def main():
    logging.basicConfig(level=logging.INFO)
    
    # This script is a wrapper to allow running specific modes via CLI
    # The actual logic is in src.analysis and src.robustness
    # We delegate to the main functions which handle argparse internally
    robustness_main()

if __name__ == '__main__':
    main()