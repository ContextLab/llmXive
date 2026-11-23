"""
Script to run the scaling study.
"""
import argparse
import logging
import sys
import os
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.experiments.scaling import main as run_scaling_study_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run scaling study")
    parser.add_argument("--columns", type=str, default="1,2,4", help="Comma-separated column counts")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/results/scaling_law.csv", help="Output CSV path")
    
    args = parser.parse_args()
    
    logger.info(f"Running scaling study with columns={args.columns}, seed={args.seed}")
    
    # Construct sys.argv for the module main
    sys.argv = [
        "run_scaling_study.py",
        "--columns", args.columns,
        "--seed", str(args.seed),
        "--output", args.output
    ]
    
    run_scaling_study_main()

if __name__ == "__main__":
    main()
