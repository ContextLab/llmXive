"""
Script to execute Ruff linting using the project's .ruff.toml configuration.
It leverages the existing linting_config utilities to run the check and
exits with a non‑zero status if any linting errors are found.
"""
import sys
from linting_config import run_ruff_check

def main() -> None:
    """
    Run Ruff linting and report the result.
    Exits with code 0 on success, 1 on failure.
    """
    success = run_ruff_check()
    if success:
        print("Ruff check passed")
        sys.exit(0)
    else:
        print("Ruff check failed")
        sys.exit(1)

if __name__ == "__main__":
    main()