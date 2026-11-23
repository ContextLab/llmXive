"""
Utilities for ensuring the NCBI SRA Toolkit is available.
This module provides functions to run shell commands, verify the
presence of the toolkit, and install it via conda if necessary.
"""

import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def run_command(command: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """
    Execute a shell command and return the CompletedProcess.

    Parameters
    ----------
    command : list[str]
        The command and its arguments.
    check : bool, optional
        If True (default), raise subprocess.CalledProcessError on non‑zero exit.

    Returns
    -------
    subprocess.CompletedProcess
        The result of the executed command.
    """
    logger.debug("Running command: %s", " ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    if check and result.returncode != 0:
        logger.error("Command failed (code %s): %s", result.returncode, result.stderr)
        result.check_returncode()
    return result

def ensure_ncbi_settings() -> bool:
    """
    Ensure ``~/.ncbi/settings`` exists with a minimal configuration.

    Returns
    -------
    bool
        True if the file exists (or was created) and appears valid,
        False otherwise.
    """
    home = Path.home()
    ncbi_dir = home / ".ncbi"
    settings_path = ncbi_dir / "settings"
    try:
        ncbi_dir.mkdir(parents=True, exist_ok=True)
        if not settings_path.is_file():
            settings_path.write_text("[NCBI]\ndefault=ftp.ncbi.nlm.nih.gov\n")
        # Very simple validation – the file must be non‑empty.
        return settings_path.stat().st_size > 0
    except Exception as e:
        logger.error("Failed to create NCBI settings file: %s", e)
        return False

def verify_sra_toolkit() -> bool:
    """
    Verify that the SRA Toolkit is installed and functional by invoking
    ``prefetch --version``. If the command runs without error, the toolkit
    is considered available.

    Returns
    -------
    bool
        True if the toolkit appears functional, False otherwise.
    """
    try:
        result = run_command(["prefetch", "--version"], check=False)
        return result.returncode == 0
    except FileNotFoundError:
        logger.warning("SRA Toolkit not found in PATH.")
        return False

def install_sra_toolkit() -> bool:
    """
    Attempt to install the SRA Toolkit via ``conda``. This function assumes
    that ``conda`` is available in the environment. It returns True if the
    installation command exits with code 0, otherwise False.

    Returns
    -------
    bool
        True if installation succeeded, False otherwise.
    """
    try:
        result = run_command(
            ["conda", "install", "-y", "-c", "bioconda", "sra-tools"]
        )
        return result.returncode == 0
    except Exception as e:
        logger.error("Failed to install SRA Toolkit: %s", e)
        return False

def main() -> None:
    """
    Entry point used by ``code/run_setup.py``. It installs the toolkit if
    missing, ensures the NCBI settings file exists, and exits with a
    non‑zero status if verification fails.
    """
    if not ensure_ncbi_settings():
        logger.error("Unable to ensure NCBI settings.")
        raise SystemExit(1)

    if not verify_sra_toolkit():
        logger.info("SRA Toolkit not detected – attempting installation.")
        if not install_sra_toolkit():
            logger.error("SRA Toolkit installation failed.")
            raise SystemExit(1)

    logger.info("SRA Toolkit is available and NCBI settings are configured.")
