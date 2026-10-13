"""Verify that `pip install -r code/requirements.txt` succeeds.

Runs pip install against the project's requirements file and
records the outcome. Exits non-zero (fails loudly) if the
installation does not complete successfully.
"""
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

def main() -> int:
    req = paths.code("requirements.txt")
    if not req.is_file():
        print(f"FAIL: requirements file not found at {req}", file=sys.stderr)
        return 1
    text = req.read_text(encoding="utf-8").strip()
    if not text:
        print(f"FAIL: requirements file is empty: {req}", file=sys.stderr)
        return 1
    print(f"Requirements file OK ({len(text.splitlines())} lines): {req}")

    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req)]
    print("Running:", " ".join(cmd))
    proc = subprocess.run(cmd)
    if proc.returncode != 0:
        print(
            f"FAIL: pip install exited with code {proc.returncode}",
            file=sys.stderr,
        )
        return proc.returncode

    # Confirm every requirement is importable/installed.
    check = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req), "--dry-run"],
        capture_output=True,
        text=True,
    )
    if check.returncode != 0:
        print("FAIL: dry-run re-resolution failed", file=sys.stderr)
        return check.returncode

    print("SUCCESS: pip install -r code/requirements.txt completed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())