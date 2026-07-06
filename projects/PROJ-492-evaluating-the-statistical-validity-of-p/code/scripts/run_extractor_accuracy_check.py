"""
Script to run the FR-002 verification check independently.
Usage: python code/scripts/run_extractor_accuracy_check.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.integration.test_extractor_accuracy import main as run_test

if __name__ == "__main__":
    sys.exit(run_test())