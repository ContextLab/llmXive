"""
Runner script for FR-002 verification test.

This script runs the extractor accuracy test and reports results.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.integration.test_extractor_accuracy import main

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
