"""
Script to run the finalize metrics process (T027b).

This script executes the finalize_metrics module to generate the final
metrics.json file from residuals and variance correlation data.
"""
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.data.finalize_metrics import main

if __name__ == "__main__":
    main()
