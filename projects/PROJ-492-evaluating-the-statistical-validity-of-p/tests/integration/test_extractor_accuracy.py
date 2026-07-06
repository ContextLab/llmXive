"""
Integration test for T036 / T072: Extractor accuracy and field coverage.
This test runs the field coverage check and ensures the extractor meets FR-002.
"""
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tests.integration.test_extractor_field_coverage import main as run_coverage_test

def main():
    """
    Runs the field coverage verification.
    Returns 0 if test passes, 1 if it fails.
    """
    print("Running T036: FR-002 Verification (Extractor Field Coverage)")
    return run_coverage_test()

if __name__ == "__main__":
    sys.exit(main())
