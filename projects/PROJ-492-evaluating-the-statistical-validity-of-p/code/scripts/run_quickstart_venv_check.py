"""
Script to verify the Quickstart Docker guide reproduces environment via requirements.txt and isolated venv.
This script runs the unit tests defined in tests/unit/test_quickstart_docker_venv.py.
It ensures Constitution Principle I is satisfied regarding environment reproducibility.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the verification tests for T095b."""
    project_root = Path(__file__).parent.parent
    test_file = project_root / "tests" / "unit" / "test_quickstart_docker_venv.py"

    if not test_file.exists():
        print(f"Error: Test file not found at {test_file}", file=sys.stderr)
        return 1

    print(f"Running verification tests for T095b: {test_file}")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file), "-v"],
            cwd=project_root,
            capture_output=False,
            check=False
        )
        return result.returncode
    except FileNotFoundError:
        print("Error: pytest not found. Please install pytest.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())