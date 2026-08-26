"""
Standalone script to execute T032: Write final metrics to data/results/output.json.

This script ensures that all prerequisites are met and then runs the T032 logic.
It can be executed directly: python code/modeling/run_t032.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modeling.save_results import main

if __name__ == "__main__":
    sys.exit(main())
