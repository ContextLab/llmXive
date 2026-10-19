"""
Utility script to run code linting.

This script is a placeholder for the project's linting command.
It can be extended to invoke tools such as flake8 or pylint.
"""

import subprocess
import sys
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def main():
    """Execute linting using flake8 (if available)."""
    try:
        subprocess.run([sys.executable, "-m", "flake8", "code/"], check=True)
        log.info("Linting completed successfully.")
    except FileNotFoundError:
        log.error("flake8 is not installed. Skipping lint.")
    except subprocess.CalledProcessError as e:
        log.error(f"Linting failed with exit code {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
