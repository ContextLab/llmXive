"""
Tool to run Ruff linting on the project codebase.
"""
import subprocess
import sys
from pathlib import Path


def run_command():
    """Run ruff linter on the code directory."""
    code_root = Path(__file__).parent.parent
    print(f"Linting code in: {code_root}")

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--config",
                str(code_root / "pyproject.toml"),
                str(code_root),
            ],
            check=True,
            capture_output=False,
        )
        print("Linting completed successfully (no errors).")
    except subprocess.CalledProcessError as e:
        print(f"Linting failed with errors. See output above.")
        sys.exit(1)


def main():
    run_command()


if __name__ == "__main__":
    main()
