import argparse
import logging
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.experiments.scaling import main as run_scaling_study_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description="Run scaling study for cortical column LLMs")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/results",
        help="Output directory for results"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of training epochs per variant"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    logging.info(f"Starting scaling study with output directory: {args.output_dir}")
    logging.info(f"Training epochs per variant: {args.epochs}")
    
    # Run scaling study
    try:
        run_scaling_study_main()
        logging.info("Scaling study completed successfully")
    except Exception as e:
        logging.error(f"Scaling study failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()