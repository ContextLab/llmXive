import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data.download import run_download_pipeline
from src.data.preprocess import run_preprocessing_pipeline
from src.models.gamm_fit import run_gamm_pipeline

def main():
    """Main entry point for the pipeline."""
    print("Starting Bird Migration Climate Analysis Pipeline...")
    
    # Step 1: Download/Generate Data
    print("Step 1: Ensuring data availability...")
    run_download_pipeline()
    
    # Step 2: Preprocess Data
    print("Step 2: Preprocessing data...")
    run_preprocessing_pipeline()
    
    # Step 3: Fit Models and Run Permutation Tests
    print("Step 3: Fitting models and running permutation tests...")
    run_gamm_pipeline()
    
    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
