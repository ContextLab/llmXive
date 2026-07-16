"""
Utility to run linters without fixing (CI mode).
Usage: python tools/lint.py
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> int:
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

def main() -> None:
    root = Path(__file__).resolve().parent.parent
    code_dir = root / "code"
    tests_dir = root / "tests"

    # Check with Black (diff mode)
    print("--- Checking formatting with Black ---")
    ret = run_command([sys.executable, "-m", "black", "--check", str(code_dir), str(tests_dir)])
    if ret != 0:
        print("Code is not formatted. Run 'python tools/format.py' to fix.")
        sys.exit(ret)

    # Check with Ruff
    print("--- Checking linting with Ruff ---")
    ret = run_command([sys.executable, "-m", "ruff", "check", str(code_dir), str(tests_dir)])
    if ret != 0:
        print("Linting errors found.")
        sys.exit(ret)

    print("All checks passed.")

if __name__ == "__main__":
    main()