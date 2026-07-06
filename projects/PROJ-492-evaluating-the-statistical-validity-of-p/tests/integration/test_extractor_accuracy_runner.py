"""
Runner script for T036 integration test.
Can be called directly to verify extraction field coverage.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.integration.test_extractor_accuracy import main as run_test

if __name__ == "__main__":
    sys.exit(run_test())
