import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.survival import main as survival_main

def main():
    """Script entry point for running survival assumption checks."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Default paths if not provided via command line
    default_args = [
        "run_survival_assumptions.py",
        "--entropy", "data/processed/entropy_results.csv",
        "--convergence", "data/processed/convergence_results_core.csv",
        "--output", "data/processed/correlation_survival.json",
        "--assumptions-output", "data/processed/survival_assumptions.json"
    ]
    
    # Override with command line args if provided
    if len(sys.argv) > 1:
        args = sys.argv[1:]
    else:
        args = default_args[1:]  # Skip script name
    
    # Create a new sys.argv for the survival_main
    sys.argv = [sys.argv[0]] + args
    survival_main()

if __name__ == "__main__":
    main()