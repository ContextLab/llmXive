"""
Run ruff static analysis on the code base.
"""

import subprocess
import sys
from pathlib import Path
import json
from datetime import datetime

def run_ruff_check(code_dir: Path) -> bool:
    """
    Run ruff check with auto‑fix and return True if exit code is 0.
    """
    result = subprocess.run(
        ["ruff", "check", "--fix", str(code_dir)],
        capture_output=True,
        text=True,
    )
    # Write the raw ruff output to logs
    log_path = Path("logs") / "ruff_check.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w") as f:
        f.write(result.stdout)
        f.write("\n")
        f.write(result.stderr)

    return result.returncode == 0

def main():
    code_dir = Path("code")
    success = run_ruff_check(code_dir)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()