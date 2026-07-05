"""
Entry point script to execute T044: Add content hashes to all artifacts.
This script is designed to be run after the pipeline has generated all data and model artifacts.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from utils.verify_hashes import main

if __name__ == "__main__":
    print("Executing T044: Adding content hashes to artifacts...")
    main()
    print("T044 completed successfully.")