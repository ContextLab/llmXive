import os
import sys
import logging
from pathlib import Path

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference import main as run_inference_main

def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Sensitivity Convergence Inference (T013b)")
    
    # Default arguments for T013b
    # Input: filtered_splits.json (from T013a context)
    # Output: convergence_results_sensitivity.csv
    # k_range: [4]
    
    # We call the main function from src.inference which handles argparse
    # But we can override defaults here if needed, or just rely on defaults
    # The src.inference.main() expects command line args.
    # Since we are running as a script, we simulate the args or pass them.
    # To ensure it runs without CLI, we can set sys.argv or call a wrapper.
    # However, the pattern in other scripts is to just call main() and let argparse handle defaults.
    
    # Set default args if not provided
    if '--input' not in sys.argv:
        sys.argv.extend(['--input', 'data/processed/filtered_splits.json'])
    if '--output' not in sys.argv:
        sys.argv.extend(['--output', 'data/processed/convergence_results_sensitivity.csv'])
    if '--model' not in sys.argv:
        # Use a smaller model for testing if the large one is not available
        # But the task requires real model. We use the config default.
        pass 
    
    run_inference_main()

if __name__ == "__main__":
    main()