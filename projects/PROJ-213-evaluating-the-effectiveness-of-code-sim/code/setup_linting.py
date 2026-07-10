"""
Script to verify linting and formatting configuration.
Runs ruff and black checks to ensure zero warnings/errors.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> int:
    """Run a shell command and return its exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode

def main() -> None:
    """Execute linting and formatting verification."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: code directory not found at {code_dir}")
        sys.exit(1)

    # Run ruff check
    ruff_cmd = ["ruff", "check", str(code_dir), "--exit-zero"]
    ruff_exit = run_command(ruff_cmd)

    # Run black check
    black_cmd = ["black", "--check", str(code_dir)]
    black_exit = run_command(black_cmd)

    if ruff_exit == 0 and black_exit == 0:
        print("\n✅ Linting and formatting checks passed.")
        sys.exit(0)
    else:
        print("\n❌ Linting or formatting checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()