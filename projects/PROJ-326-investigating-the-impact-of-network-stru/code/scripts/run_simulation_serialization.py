"""
Script to run simulation and serialize results for T029.

This script is invoked by the run-book to ensure that simulation results
are properly serialized to data/analysis/simulation_results.json.
"""
import argparse
import logging
import sys
from pathlib import Path

# Add code/src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.analysis.serialize_simulation import main as serialization_main

def setup_logging():
    """Initialize logging for this script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description="Run simulation and serialize results.")
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to the configuration file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Override the default output file path."
    )
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        serialization_main(args.config, args.output)
    except Exception as e:
        logging.error(f"Failed to run simulation serialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()