"""
T005b: Linting Verification Script.
Runs `ruff check .` and `black --check .` in the project root.
Exits with code 0 if both pass, non-zero otherwise.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # Determine the project root relative to this script's location
    # The script is in projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/
    project_root = Path(__file__).resolve().parent

    print(f"Running linters in: {project_root}")
    os.chdir(project_root)

    # 1. Run Ruff Check
    print("\n--- Running ruff check . ---")
    ruff_result = subprocess.run(
        ["ruff", "check", "."],
        capture_output=True,
        text=True
    )
    if ruff_result.returncode != 0:
        print("Ruff Check FAILED:")
        print(ruff_result.stdout)
        print(ruff_result.stderr)
        return 1
    else:
        print("Ruff Check PASSED.")

    # 2. Run Black Check
    print("\n--- Running black --check . ---")
    black_result = subprocess.run(
        ["black", "--check", "."],
        capture_output=True,
        text=True
    )
    if black_result.returncode != 0:
        print("Black Check FAILED:")
        print(black_result.stdout)
        print(black_result.stderr)
        return 1
    else:
        print("Black Check PASSED.")

    print("\n--- All linting checks passed successfully. ---")
    return 0

if __name__ == "__main__":
    sys.exit(main())
