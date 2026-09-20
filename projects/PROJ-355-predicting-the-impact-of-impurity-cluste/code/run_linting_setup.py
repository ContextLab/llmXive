"""
Runner script for the linting setup process.
"""
import sys
from pathlib import Path
from config_linting import main as config_linting_main
from linting_setup import main as linting_setup_main


def main() -> int:
    """
    Execute the full linting setup and configuration.
    """
    print("=== Running Linting Setup ===")

    # Step 1: Install tools if missing
    exit_code = linting_setup_main()
    if exit_code != 0:
        print("Failed to install tools.")
        return exit_code

    # Step 2: Verify and configure
    exit_code = config_linting_main()
    if exit_code != 0:
        print("Failed to verify or configure tools.")
        return exit_code

    print("=== Linting Setup Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())