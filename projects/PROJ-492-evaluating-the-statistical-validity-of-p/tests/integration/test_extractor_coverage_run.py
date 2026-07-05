"""
Wrapper script to run the FR-002 test and ensure it is executed as part of the verification suite.
This script is designed to be called by CI or manually to verify the extraction coverage.
"""
import subprocess
import sys
from pathlib import Path

def main():
    test_script = Path(__file__).parent / "test_extractor_coverage.py"
    if not test_script.exists():
        print(f"Error: Test script {test_script} not found.")
        sys.exit(1)

    print(f"Running FR-002 verification test: {test_script}")
    result = subprocess.run(
        [sys.executable, str(test_script)],
        cwd=test_script.parent.parent.parent,
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    sys.exit(result.returncode)

if __name__ == "__main__":
    main()