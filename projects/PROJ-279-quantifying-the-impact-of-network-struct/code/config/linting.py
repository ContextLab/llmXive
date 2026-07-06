"""
Linting and formatting utilities for the project.
Wraps ruff and black commands.
"""
import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def run_ruff_check() -> bool:
    """Run ruff check on the code directory."""
    logger.info("Running ruff check...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "code"],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Ruff check failed:\n{e.stdout}\n{e.stderr}")
        return False

def run_ruff_fix() -> bool:
    """Run ruff check with --fix on the code directory."""
    logger.info("Running ruff fix...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--fix", "code"],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Ruff fix failed:\n{e.stdout}\n{e.stderr}")
        return False

def run_black_check() -> bool:
    """Run black --check on the code directory."""
    logger.info("Running black check...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "code"],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Black check failed:\n{e.stdout}\n{e.stderr}")
        return False

def run_black_format() -> bool:
    """Run black --check on the code directory."""
    logger.info("Running black format...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "code"],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Black format failed:\n{e.stdout}\n{e.stderr}")
        return False

def main():
    """Main entry point for linting tools."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python -m config.linting [check|fix|format]")
        print("  check  : Run ruff check and black check")
        print("  fix    : Run ruff fix")
        print("  format : Run black format")
        sys.exit(1)

    command = sys.argv[1]

    success = True
    if command == "check":
        success = run_ruff_check() and run_black_check()
    elif command == "fix":
        success = run_ruff_fix()
    elif command == "format":
        success = run_black_format()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

    if success:
        logger.info("Linting/Formatting checks passed.")
        sys.exit(0)
    else:
        logger.error("Linting/Formatting checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()