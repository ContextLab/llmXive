"""
Script to initialize the training log file structure.
This script creates the data/raw/training_log.json file with the initial schema.
"""
import os
import json
import sys

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def init_training_log():
    """
    Initialize data/raw/training_log.json with the required schema.
    """
    log_path = os.path.join("data", "raw", "training_log.json")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Define the initial schema structure
    initial_log = {
        "metadata": {
            "version": "1.0",
            "created_at": None,
            "schema": {
                "entries": [
                    {
                        "step": "int",
                        "regime": "str",
                        "seed": "int",
                        "reward": "float",
                        "loss": "float",
                        "accuracy": "float",
                        "entropy": "float",
                        "lambda_weight": "float",
                        "timestamp": "str (ISO8601)"
                    }
                ]
            }
        },
        "entries": []
    }
    
    # Check if file already exists to avoid overwriting
    if os.path.exists(log_path):
        print(f"File {log_path} already exists. Skipping initialization.")
        return
    
    try:
        with open(log_path, 'w') as f:
            json.dump(initial_log, f, indent=2)
        print(f"Successfully initialized {log_path}")
    except Exception as e:
        print(f"Error initializing log file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_training_log()
