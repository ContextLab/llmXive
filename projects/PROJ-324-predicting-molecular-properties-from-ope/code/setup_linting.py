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
    Main entry point for setting up linting tools.
    """
    run_command("pip install ruff black")
    run_command("ruff --version")
    run_command("black --version")

if __name__ == "__main__":
    main()
