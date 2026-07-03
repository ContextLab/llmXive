"""Test wrapper for CI pipeline execution.

Ensures the CI pipeline runner can be imported and executed
without errors, suitable for CI validation.
"""
import sys
from pathlib import Path

def main() -> int:
    """Run the CI pipeline test wrapper."""
    try:
        from run_full_pipeline_ci import main as ci_main
        return ci_main()
    except Exception as e:
        print(f"CI Pipeline Test Failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
