import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from src.data.download import fetch_evalverse_dataset
from src.data.download import main as download_main
from src.models.train import main as train_main
from src.models.evaluate import main as evaluate_main

def main():
    print("=== Running Full Pipeline ===")
    
    # Step 1: Download data
    print("Step 1: Fetching dataset...")
    try:
        fetch_evalverse_dataset()
    except Exception as e:
        print(f"Data fetch failed: {e}")
        # In a real pipeline, we might exit here. For now, we continue if data exists.
    
    # Step 2: Train models
    print("Step 2: Training models...")
    train_main()
    
    # Step 3: Evaluate
    print("Step 3: Evaluating baselines...")
    evaluate_main()
    
    print("=== Pipeline Complete ===")

if __name__ == "__main__":
    main()