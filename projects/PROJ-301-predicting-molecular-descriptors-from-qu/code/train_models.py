"""
train_models.py: Entry point for model training.

This script serves as the canonical entry point for the model training logic
as referenced by the run-book and internal tests. It delegates to the implementation
in `code/04_model_training.py`.
"""

import sys
import os

# Ensure the code directory is in the path for relative imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the main logic from the implementation module
from code_04_model_training import main as training_main

def main():
    """
    Entry point for the train_models command.
    Delegates execution to the training module.
    """
    print("Starting Model Training Pipeline (via code/train_models.py)...")
    try:
        training_main()
        print("Model Training completed successfully.")
    except Exception as e:
        print(f"Model Training failed: {e}")
        raise

if __name__ == "__main__":
    main()
