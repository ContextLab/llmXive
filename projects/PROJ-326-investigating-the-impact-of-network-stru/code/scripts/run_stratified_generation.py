"""
Script wrapper for running stratified generation.
"""
import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.generators.stratified_runner import run_stratified_generation

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    parser = argparse.ArgumentParser(description="Run stratified generation script.")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file.")
    parser.add_argument("--output", type=str, default="data/raw", help="Output directory.")
    parser.add_argument("--log", type=str, default="data/run_log.json", help="Log file path.")
    args = parser.parse_args()

    setup_logging()

    try:
        result = run_stratified_generation(
            config_path=args.config,
            output_dir=args.output,
            log_path=args.log
        )
        print(f"Stratified generation completed. Summary: {result}")
    except Exception as e:
        logging.error(f"Failed to run stratified generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
