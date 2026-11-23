"""
Runner script for T014b: Validate sampling distribution preservation.

This script executes the validation of stratified sampling distribution
preservation as specified in FR-015 and US-1.

Usage:
    python code/data/validate_sampling_run.py
    
This script expects:
    - data/processed/raw.parquet (original dataset before sampling)
    - data/processed/preprocessed.parquet (sampled dataset after processing)

It will output:
    - data/metrics/sampling_validation.json (validation results)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.validate_sampling import main
from utils.config import set_seed

def main_runner():
    """Main entry point for the validation runner."""
    # Set seed for reproducibility
    set_seed(42)
    
    # Define paths
    project_root = Path(__file__).parent.parent
    original_path = project_root / 'data' / 'processed' / 'raw.parquet'
    sampled_path = project_root / 'data' / 'processed' / 'preprocessed.parquet'
    output_path = project_root / 'data' / 'metrics' / 'sampling_validation.json'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run validation
    print("Starting sampling distribution validation...")
    print(f"Original dataset: {original_path}")
    print(f"Sampled dataset: {sampled_path}")
    print(f"Output file: {output_path}")
    print("-" * 60)
    
    try:
        results = main(
            original_path=original_path,
            sampled_path=sampled_path,
            output_path=output_path
        )
        
        print("-" * 60)
        print("Validation completed successfully!")
        print(f"Results saved to: {output_path}")
        
        return 0
        
    except Exception as e:
        print(f"Validation failed with error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main_runner())