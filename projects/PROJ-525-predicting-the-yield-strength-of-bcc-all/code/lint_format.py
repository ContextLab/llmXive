import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, cwd: Path = None) -> int:
    """Runs a shell command and returns the exit code."""
    try:
        result = subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        return 1

def main():
    """Entry point for linting and formatting."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    print("Running Ruff (Linting)...")
    ruff_cmd = ["ruff", "check", str(code_dir)]
    ruff_code = run_command(ruff_cmd, cwd=project_root)

    print("\nRunning Black (Formatting)...")
    black_cmd = ["black", "--check", str(code_dir)]
    black_code = run_command(black_cmd, cwd=project_root)

    if ruff_code == 0 and black_code == 0:
        print("\nAll checks passed!")
        sys.exit(0)
    else:
        print("\nSome checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
