"""
Helper script to execute the full contract test suite.
This is invoked by the task runner to ensure that the newly added
schemas and test file are discoverable and pass validation.
"""
import subprocess
import sys

def main():
    # Run pytest on the top‑level tests directory
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "tests/contract"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())