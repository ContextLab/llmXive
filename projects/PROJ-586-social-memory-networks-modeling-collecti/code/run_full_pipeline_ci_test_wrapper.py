"""Test wrapper for CI pipeline to verify resource recording.

This script runs the full pipeline and verifies that results are recorded.
"""
import sys
from pathlib import Path

# Ensure we can import sibling modules
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from run_full_pipeline_ci import main as ci_main


def main() -> int:
    """Run the CI pipeline and return exit code."""
    return ci_main()


if __name__ == "__main__":
    sys.exit(main())
