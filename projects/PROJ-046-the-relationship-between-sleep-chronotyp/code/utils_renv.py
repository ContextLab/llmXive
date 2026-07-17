import subprocess
import sys
import os
import json
from typing import List, Optional
from pathlib import Path

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def check_r_version(min_version: str = "4.3") -> bool:
    """Check if R version meets the minimum requirement."""
    try:
        result = subprocess.run(
            ["R", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        if result.returncode != 0:
            return False

        output = result.stdout.decode('utf-8')
        # Parse version from output (format: "R version X.Y.Z ...")
        for line in output.split('\n'):
            if line.startswith('R version'):
                parts = line.split()
                if len(parts) >= 3:
                    version = parts[2]
                    # Compare versions
                    major, minor, patch = version.split('.')[:3]
                    min_major, min_minor, min_patch = min_version.split('.')
                    if int(major) > int(min_major):
                        return True
                    elif int(major) == int(min_major):
                        if int(minor) > int(min_minor):
                            return True
                        elif int(minor) == int(min_minor):
                            if int(patch) >= int(min_patch):
                                return True
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        return False

def verify_packages(packages: List[str], logger=None) -> bool:
    """Verify that required R packages are installed."""
    if logger is None:
        from utils_logging import get_pipeline_logger
        logger = get_pipeline_logger()

    missing_packages = []
    for pkg in packages:
        try:
            result = subprocess.run(
                ["R", "--slave", "-e", f"library({pkg})"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            if result.returncode != 0:
                missing_packages.append(pkg)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            missing_packages.append(pkg)

    if missing_packages:
        logger.error(f"Missing R packages: {', '.join(missing_packages)}")
        return False

    logger.info("All required R packages are installed.")
    return True

def initialize_renv(packages: List[str], logger=None) -> bool:
    """Initialize renv and install required packages."""
    if logger is None:
        from utils_logging import get_pipeline_logger
        logger = get_pipeline_logger()

    project_root = get_project_root()
    renv_dir = project_root / "renv"

    # Check if renv is already initialized
    if (project_root / "renv.lock").exists() or renv_dir.exists():
        logger.info("renv is already initialized.")
        return verify_packages(packages, logger)

    # Initialize renv
    logger.info("Initializing renv...")
    try:
        result = subprocess.run(
            ["R", "--slave", "-e", "renv::init()"],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )
        if result.returncode != 0:
            logger.error(f"Failed to initialize renv: {result.stderr.decode('utf-8')}")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.error(f"Failed to run R: {str(e)}")
        return False

    # Install packages
    logger.info(f"Installing packages: {', '.join(packages)}")
    packages_str = 'c(' + ', '.join([f'"{pkg}"' for pkg in packages]) + ')'
    try:
        result = subprocess.run(
            ["R", "--slave", "-e", f"renv::install({packages_str})"],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=600
        )
        if result.returncode != 0:
            logger.error(f"Failed to install packages: {result.stderr.decode('utf-8')}")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.error(f"Failed to run R: {str(e)}")
        return False

    logger.info("renv initialized and packages installed.")
    return verify_packages(packages, logger)

def main():
    """Main entry point for R environment setup."""
    from utils_logging import get_pipeline_logger
    logger = get_pipeline_logger()

    required_packages = [
        "tidyverse", "lme4", "car", "effectsize", "pwr",
        "rmarkdown", "knitr", "data.table", "testthat", "lintr"
    ]

    # Check R version
    if not check_r_version():
        logger.error("R 4.3+ is required. Please install R 4.3 or higher.")
        sys.exit(1)

    logger.info("R version check passed.")

    # Initialize renv and install packages
    if not initialize_renv(required_packages, logger):
        logger.error("Failed to initialize R environment.")
        sys.exit(1)

    logger.info("R environment setup completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()