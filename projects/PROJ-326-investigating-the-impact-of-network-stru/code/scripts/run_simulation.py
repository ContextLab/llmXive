"""
Script wrapper to invoke the simulation runner.

This script provides a clean entry point for the quickstart run-book.
It delegates to code/src/simulation/run_simulation.py.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.simulation.run_simulation import main as run_simulation_main, setup_logging

def main():
    """Wrapper entry point."""
    parser = argparse.ArgumentParser(description="Run energy propagation simulations.")
    parser.add_argument("--config", type=str, help="Path to config.yaml")
    parser.add_argument("--manifest", type=str, help="Path to global batch manifest")
    parser.add_argument("--output", type=str, help="Path to output results JSON")
    parser.add_argument("--log", type=str, help="Path to run log JSON")
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(Path(args.log) if args.log else None)
    
    # Call the main simulation runner
    return run_simulation_main()

if __name__ == "__main__":
    sys.exit(main())