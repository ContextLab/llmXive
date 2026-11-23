"""
QIIME 2 Environment Setup and CLI Wrapper

This module provides utilities to install, configure, and verify QIIME 2
via Conda/Mamba, and to execute QIIME 2 CLI commands.

It ensures the environment is ready for downstream tasks (T018) that
require `qiime demux summarize` and `qiime dada2 denoise-paired`.
"""

import os
import subprocess
import sys
import logging
from pathlib import Path
from typing import List, Optional, Tuple

# Configure logger
logger = logging.getLogger(__name__)

# QIIME 2 version to install (stable release)
# Using a specific release ensures reproducibility.
# This version is compatible with standard Linux/Ubuntu environments.
QIIME2_VERSION = "2023.9"
CONDA_ENV_NAME = "qiime2-amplicon"
ENV_FILE_PATH = Path("data/processed/conda_env_qiime2.yaml")

def check_conda_installed() -> bool:
    """
    Checks if conda or mamba is installed and available in PATH.

    Returns:
        bool: True if conda/mamba is found, False otherwise.
    """
    try:
        result = subprocess.run(
            ["which", "conda"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("Conda found at: %s", result.stdout.strip())
            return True

        result_mamba = subprocess.run(
            ["which", "mamba"],
            capture_output=True,
            text=True,
            check=False
        )
        if result_mamba.returncode == 0:
            logger.info("Mamba found at: %s", result_mamba.stdout.strip())
            return True

        logger.warning("Neither conda nor mamba found in PATH.")
        return False
    except FileNotFoundError:
        logger.error("Could not execute conda/mamba check command.")
        return False

def create_qiime2_environment() -> bool:
    """
    Creates the QIIME 2 Conda environment if it does not exist.

    This function generates a temporary environment YAML file with the
    specific QIIME 2 package and runs `conda create` (or `mamba create`).

    Returns:
        bool: True if environment creation was successful, False otherwise.
    """
    if not check_conda_installed():
        logger.error("Conda/Mamba is required but not installed.")
        return False

    # Ensure the directory for the env file exists
    ENV_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write the environment file
    # Using the official QIIME 2 channel and version
    env_content = f"""
    name: {CONDA_ENV_NAME}
    channels:
      - conda-forge
      - bioconda
      - qiime2
      - defaults
    dependencies:
      - qiime2={QIIME2_VERSION}
      - qiime2-amplicon={QIIME2_VERSION}
      - python>=3.8
    """

    try:
        with open(ENV_FILE_PATH, 'w') as f:
            f.write(env_content)
        logger.info(f"Environment file written to: {ENV_FILE_PATH}")
    except IOError as e:
        logger.error(f"Failed to write environment file: {e}")
        return False

    # Determine command (mamba preferred for speed, fallback to conda)
    cmd_base = "mamba" if subprocess.run(["which", "mamba"], capture_output=True).returncode == 0 else "conda"

    logger.info(f"Creating environment '{CONDA_ENV_NAME}' using {cmd_base}...")
    try:
        # -y for yes, --file for yaml
        subprocess.run(
            [cmd_base, "create", "-n", CONDA_ENV_NAME, "--file", str(ENV_FILE_PATH), "-y"],
            check=True
        )
        logger.info(f"Environment '{CONDA_ENV_NAME}' created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create environment: {e}")
        # Clean up env file if creation fails to avoid confusion
        if ENV_FILE_PATH.exists():
            ENV_FILE_PATH.unlink()
        return False

def verify_qiime2_installation() -> bool:
    """
    Verifies that QIIME 2 is installed and the CLI is functional.

    Runs `qiime --version` inside the activated environment.

    Returns:
        bool: True if version check passes, False otherwise.
    """
    if not check_conda_installed():
        return False

    logger.info("Verifying QIIME 2 installation...")
    try:
        # Use conda run to execute without explicitly activating shell
        result = subprocess.run(
            ["conda", "run", "-n", CONDA_ENV_NAME, "qiime", "--version"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            logger.info("QIIME 2 verification successful: %s", result.stdout.strip())
            return True
        else:
            logger.error(f"QIIME 2 verification failed: {result.stderr}")
            return False
    except FileNotFoundError:
        logger.error("Conda command not found during verification.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        return False

def run_qiime2_command(command_args: List[str]) -> Tuple[bool, str, str]:
    """
    Executes a QIIME 2 CLI command within the configured environment.

    Args:
        command_args: List of arguments for the qiime command (e.g., ['demux', 'summarize', ...]).

    Returns:
        Tuple[bool, str, str]: (success, stdout, stderr)
    """
    if not verify_qiime2_installation():
        return False, "", "QIIME 2 environment not verified. Cannot run command."

    cmd = ["conda", "run", "-n", CONDA_ENV_NAME, "qiime"] + command_args
    logger.info(f"Running QIIME 2 command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("QIIME 2 command succeeded.")
            return True, result.stdout, result.stderr
        else:
            logger.error(f"QIIME 2 command failed with code {result.returncode}: {result.stderr}")
            return False, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Error executing QIIME 2 command: {e}")
        return False, "", str(e)

def setup_qiime2_environment() -> bool:
    """
    Main entry point to setup the QIIME 2 environment.
    Checks installation, creates env if needed, and verifies.

    Returns:
        bool: True if setup is complete and verified, False otherwise.
    """
    if not check_conda_installed():
        logger.error("Conda/Mamba is required to setup QIIME 2.")
        return False

    if not verify_qiime2_installation():
        logger.info("QIIME 2 not found in environment. Attempting to create...")
        if not create_qiime2_environment():
            logger.error("Failed to create QIIME 2 environment.")
            return False

        if not verify_qiime2_installation():
            logger.error("QIIME 2 verification failed after creation.")
            return False

    logger.info("QIIME 2 environment is ready.")
    return True

def main():
    """
    Command-line interface for setting up QIIME 2.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    success = setup_qiime2_environment()
    if success:
        logger.info("QIIME 2 setup completed successfully.")
        sys.exit(0)
    else:
        logger.error("QIIME 2 setup failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
