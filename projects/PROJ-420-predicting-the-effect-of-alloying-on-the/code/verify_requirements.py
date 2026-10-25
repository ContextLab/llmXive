"""
Verify that the pinned dependencies can be installed without conflicts.

This script runs ``pip install -r code/requirements.txt`` in a subprocess.
It exits with status code 0 on success and prints a short summary.
"""

import subprocess
import sys
from pathlib import Path

def main() -> None:
    req_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    if not req_path.is_file():
        print(f"Requirements file not found at {req_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Installing dependencies from {req_path} ...")
    # Using '--quiet' to suppress verbose output; '--no-deps' is omitted
    # because we want the full resolution of transitive dependencies.
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    print(result.stdout)

    if result.returncode != 0:
        print("Dependency installation failed.", file=sys.stderr)
        sys.exit(result.returncode)

    print("All pinned dependencies installed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
