import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

def run_command(command: str) -> None:
    """
    Run a shell command.
    
    Args:
        command: Command string to execute.
    """
    subprocess.run(command, shell=True, check=True)

def check_code() -> None:
    """
    Check code for linting errors using ruff.
    """
    run_command("ruff check code/")

def fix_code() -> None:
    """
    Fix code formatting and linting issues.
    """
    run_command("ruff check --fix code/")
    run_command("black code/")

def main() -> None:
    """
    Main entry point for linting and formatting configuration.
    """
    fix_code()

if __name__ == "__main__":
    main()
