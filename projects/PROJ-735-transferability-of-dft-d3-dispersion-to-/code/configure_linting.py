import os
import subprocess
import sys
from pathlib import Path
from logger import get_logger, error, info

def ensure_config_files():
    """Create .flake8 and pyproject.toml (for black) if they don't exist."""
    root = Path(__file__).parent.parent
    flake8_cfg = root / ".flake8"
    pyproject_cfg = root / "pyproject.toml"

    if not flake8_cfg.exists():
        with open(flake8_cfg, "w") as f:
            f.write("[flake8]\nmax-line-length = 88\nextend-ignore = E203\n")
        info("Created .flake8 configuration")

    if not pyproject_cfg.exists():
        with open(pyproject_cfg, "w") as f:
            f.write("[tool.black]\nline-length = 88\n")
        info("Created pyproject.toml for black configuration")

def run_flake8():
    """Run flake8 on the code/ and tests/ directories."""
    root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "flake8", "code", "tests"],
        cwd=root,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        info("flake8: No issues found.")
        return True
    else:
        error("flake8 found issues:")
        print(result.stdout)
        print(result.stderr)
        return False

def run_black():
    """Run black on the code/ and tests/ directories."""
    root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "code", "tests"],
        cwd=root,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        info("black: Code is already formatted correctly.")
        return True
    else:
        error("black found formatting issues. Running formatter...")
        format_result = subprocess.run(
            [sys.executable, "-m", "black", "code", "tests"],
            cwd=root,
            capture_output=True,
            text=True
        )
        if format_result.returncode == 0:
            info("black: Code formatted successfully.")
            return True
        else:
            error("black: Failed to format code.")
            print(format_result.stderr)
            return False

def run_isort():
    """Run isort on the code/ and tests/ directories."""
    root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "isort", "--check-only", "code", "tests"],
        cwd=root,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        info("isort: Imports are sorted correctly.")
        return True
    else:
        error("isort found import sorting issues. Running sorter...")
        sort_result = subprocess.run(
            [sys.executable, "-m", "isort", "code", "tests"],
            cwd=root,
            capture_output=True,
            text=True
        )
        if sort_result.returncode == 0:
            info("isort: Imports sorted successfully.")
            return True
        else:
            error("isort: Failed to sort imports.")
            print(sort_result.stderr)
            return False

def main():
    """Main entry point to run all linting and formatting checks."""
    logger = get_logger(__name__)
    logger.info("Starting linting and formatting checks...")

    ensure_config_files()

    flake8_ok = run_flake8()
    black_ok = run_black()
    isort_ok = run_isort()

    if flake8_ok and black_ok and isort_ok:
        logger.info("All linting and formatting checks passed.")
        return 0
    else:
        logger.error("Some linting or formatting checks failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
