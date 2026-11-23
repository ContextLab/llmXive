"""
Helper script to execute the project's full pytest suite.

The script is deliberately tiny: it invokes ``pytest -q`` via ``subprocess``
and propagates the exit code.  The task T1224 verification checks that the
script exits with status ``0``.
"""

import subprocess
import sys
from pathlib import Path

def main() -> None:
    """
    Run ``pytest -q`` in the repository root and exit with the same return
    code.  Any failure will cause a non‑zero exit status, which the
    verification step interprets as a failure of the test suite.
    """
    # Ensure we are executing from the repository root
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["pytest", "-q"],
        cwd=str(repo_root),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
