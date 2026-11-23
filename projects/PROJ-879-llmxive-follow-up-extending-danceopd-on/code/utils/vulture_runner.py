"""
Wrapper script to run vulture on the code directory and report unused code.
This satisfies the verification requirement for T035b.
"""

import subprocess
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).parent.parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: {code_dir} does not exist.")
        sys.exit(1)

    # Try to run vulture
    try:
        result = subprocess.run(
            ["vulture", str(code_dir), "--min-confidence", "100"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("Error: vulture is not installed. Run: pip install vulture")
        sys.exit(1)

    if result.returncode == 0:
        print("No unused code found.")
        sys.exit(0)
    else:
        print("Unused code found:")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()