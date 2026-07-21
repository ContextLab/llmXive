import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> None:
    """Run a command and raise an error if it fails."""
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Successfully ran: {' '.join(cmd)}")
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr.decode()}")
        sys.exit(1)

def main() -> None:
    """Run ruff (lint + fix) and black on the codebase."""
    project_root = Path(__file__).resolve().parent.parent.parent
    print(f"Running linters and formatters in {project_root}")

    # Run Ruff (linting and auto-fix)
    # Using ruff check to lint and --fix to auto-fix simple issues
    run_command([sys.executable, "-m", "ruff", "check", "--fix", str(project_root)])

    # Run Black (formatting)
    run_command([sys.executable, "-m", "black", str(project_root)])

    print("Linting and formatting complete.")

if __name__ == "__main__":
    main()