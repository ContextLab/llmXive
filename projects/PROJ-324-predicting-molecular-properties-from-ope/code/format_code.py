import subprocess
import sys
from pathlib import Path

def run_command(command: str) -> None:
    """
    Run a shell command.
    
    Args:
        command: Command string to execute.
    """
    subprocess.run(command, shell=True, check=True)

def main() -> None:
    """
    Main entry point for formatting code.
    """
    run_command("black code/")
    run_command("ruff check --fix code/")

if __name__ == "__main__":
    main()
