"""
Utility to run black and ruff fixers.
Usage: python tools/format.py
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> int:
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return e.returncode

def main() -> None:
    root = Path(__file__).resolve().parent.parent
    code_dir = root / "code"
    tests_dir = root / "tests"

    # Format with Black
    print("--- Formatting with Black ---")
    ret = run_command([sys.executable, "-m", "black", str(code_dir), str(tests_dir)])
    if ret != 0:
        sys.exit(ret)

    # Lint and fix with Ruff
    print("--- Linting and fixing with Ruff ---")
    ret = run_command([sys.executable, "-m", "ruff", "check", "--fix", str(code_dir), str(tests_dir)])
    if ret != 0:
        # Ruff returns non-zero if errors remain, which is expected in CI but we warn here
        print("Ruff found remaining issues.")
        # Optional: run ruff format if enabled in future
        # ret = run_command([sys.executable, "-m", "ruff", "format", str(code_dir), str(tests_dir)])

    print("Formatting complete.")

if __name__ == "__main__":
    main()
