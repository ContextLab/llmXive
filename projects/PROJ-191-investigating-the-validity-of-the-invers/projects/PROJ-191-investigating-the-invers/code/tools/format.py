"""
Tool to run Black formatting on the project codebase.
"""
import subprocess
import sys
from pathlib import Path


def run_command():
    """Run black formatter on the code directory."""
    code_root = Path(__file__).parent.parent
    print(f"Formatting code in: {code_root}")

    try:
        subprocess.run(
            [sys.executable, "-m", "black", "--config", str(code_root / "pyproject.toml"), str(code_root)],
            check=True,
            capture_output=False,
        )
        print("Formatting completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Formatting failed: {e}")
        sys.exit(1)


def main():
    run_command()


if __name__ == "__main__":
    main()
