"""
Linting and Formatting tool wrapper for the llmXive project.

Executes Ruff (linting) and Black (formatting) on the project codebase.
"""
import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"✓ {description} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run linting and formatting tools.")
    parser.add_argument(
        "--mode",
        choices=["lint", "format", "both"],
        default="both",
        help="Mode of operation: lint, format, or both."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to automatically fix linting issues (ruff check --fix)."
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)

    success = True

    if args.mode in ["lint", "both"]:
        lint_cmd = ["ruff", "check", str(code_dir)]
        if args.fix:
            lint_cmd.insert(2, "--fix")
        if not run_command(lint_cmd, "Ruff Linting"):
            success = False

    if args.mode in ["format", "both"]:
        format_cmd = ["black", str(code_dir)]
        if not run_command(format_cmd, "Black Formatting"):
            success = False

    if success:
        print("\nAll checks passed.")
        sys.exit(0)
    else:
        print("\nSome checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
