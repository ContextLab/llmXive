"""
Script to execute the generation of the Generalization Set (Test Set).
This script assumes T011 and T012 have been run and training CSVs exist in data/raw/.
"""
import os
import sys
import argparse
from pathlib import Path

# Ensure code directory is in path
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from generators.test_set_generator import main as test_set_main

def main():
    parser = argparse.ArgumentParser(description="Run Test Set Generation Pipeline")
    parser.add_argument('--output', type=str, default='data/raw/test_set.csv',
                        help='Output path for the test set')
    parser.add_argument('--training-dir', type=str, default='data/raw',
                        help='Directory containing training CSVs')
    parser.add_argument('--count', type=int, default=500,
                        help='Number of test samples to generate')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed')
    
    args = parser.parse_args()
    
    # Identify training files
    training_dir = Path(args.training_dir)
    training_files = list(training_dir.glob('high_entropy.csv')) + \
                     list(training_dir.glob('low_entropy.csv')) + \
                     list(training_dir.glob('target_specific.csv'))
    
    if not training_files:
        print("Error: No training CSV files found in the specified directory.")
        print("Please ensure T012 (dataset generation) has been run first.")
        sys.exit(1)
    
    file_paths = [str(f) for f in training_files]
    print(f"Found training files: {file_paths}")
    
    # Prepare arguments for the generator
    sys.argv = [
        'run_test_set_generation.py',
        '--output', args.output,
        '--count', str(args.count),
        '--seed', str(args.seed),
        '--training-files'
    ] + file_paths
    
    test_set_main()

if __name__ == "__main__":
    main()