import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.robustness import merge_convergence_results, main as robustness_main

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Default paths based on task description
    core_path = "data/processed/convergence_results_core.csv"
    sensitivity_path = "data/processed/convergence_results_sensitivity.csv"
    output_path = "data/processed/convergence_results_merged.csv"
    
    # Allow overrides via arguments if run directly with args
    if len(sys.argv) > 1:
        # Simple arg parsing if called like: python run_merge_convergence.py --input1 ... --input2 ... --output ...
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--input1", type=str, default=core_path)
        parser.add_argument("--input2", type=str, default=sensitivity_path)
        parser.add_argument("--output", type=str, default=output_path)
        args = parser.parse_args()
        core_path = args.input1
        sensitivity_path = args.input2
        output_path = args.output

    logging.info(f"Starting merge: {core_path} + {sensitivity_path} -> {output_path}")
    
    merge_convergence_results(core_path, sensitivity_path, output_path)
    
    logging.info(f"Merge complete. Output saved to {output_path}")

if __name__ == "__main__":
    main()