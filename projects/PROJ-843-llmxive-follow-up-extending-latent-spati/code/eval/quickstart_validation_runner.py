"""
Runner script for T024: Quickstart Validation.
This script executes the validation logic defined in quickstart_validator.py
and ensures the pipeline artifacts are present and valid on a CPU-only environment.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from eval.quickstart_validator import main

if __name__ == "__main__":
    print("Starting T024: Quickstart Validation on CPU-only environment...")
    main()
    print("T024 Validation Complete.")