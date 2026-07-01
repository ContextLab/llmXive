"""
Entry point for running the preprocessing pipeline.
Executes filtering (T014) and surprisal computation (T015, T016).
"""
import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from preprocess import run_preprocessing_pipeline
from config import set_seed, get_data_dir

def main():
    """Run the preprocessing pipeline."""
    # Set random seed for reproducibility
    set_seed(42)
    
    # Define directories
    data_dir = get_data_dir()
    raw_input_dir = data_dir / 'raw'
    filtered_output_dir = data_dir / 'filtered'
    processed_output_dir = data_dir / 'processed'
    exclusion_log_path = data_dir / 'exclusion_log.json'
    
    # Ensure directories exist
    raw_input_dir.mkdir(parents=True, exist_ok=True)
    filtered_output_dir.mkdir(parents=True, exist_ok=True)
    processed_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if raw data exists
    if not any(raw_input_dir.glob('*')):
        print("No raw datasets found. Please run download.py first.")
        sys.exit(1)
    
    # Run preprocessing
    print("Running preprocessing pipeline...")
    results = run_preprocessing_pipeline(
        raw_input_dir=str(raw_input_dir),
        filtered_output_dir=str(filtered_output_dir),
        processed_output_dir=str(processed_output_dir),
        exclusion_log_path=str(exclusion_log_path)
    )
    
    # Save results summary
    results_path = processed_output_dir / 'preprocessing_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Preprocessing complete. Results saved to {results_path}")
    print(f"Standardized output: {results['output_file']}")
    
    return results

if __name__ == '__main__':
    main()
