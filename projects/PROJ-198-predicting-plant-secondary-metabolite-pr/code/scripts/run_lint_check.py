#!/usr/bin/env python3
"""
Lint and formatting verification script.
Ensures that the project's codebase conforms to the configured
linting (ruff) and formatting (black) standards.
"""
import subprocess
import sys
from code.utils.logging import get_logger, setup_logging


def main() -> int:
    """Run ruff and black checks; return exit code."""
    setup_logging()
    logger = get_logger(__name__)

    commands = [
        ["ruff", "--quiet", "."],
        ["black", "--check", "."],
    ]

    for cmd in commands:
        try:
            logger.info("Running: %s", " ".join(cmd))
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(
                "Command failed with exit code %s: %s", e.returncode, " ".join(cmd)
            )
            return e.returncode
        except FileNotFoundError:
            logger.error("Command not found: %s", cmd[0])
            return 1
    logger.info("All linting checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
