"""
QIIME2 Environment Setup and CLI Configuration Script.

This script configures the Conda/Mamba environment for QIIME2 and provides
a CLI wrapper to ensure the environment is active before running QIIME2 commands.

It verifies the installation of QIIME2 and its dependencies (dada2, demux, etc.)
and provides a helper function to execute QIIME2 commands within the correct
environment context.
"""
import os
import subprocess
import sys
import logging
from pathlib import Path
from typing import List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# QIIME2 Environment Configuration
QIIME2_ENV_NAME = "qiime2-2023.9"
QIIME2_VERSION = "2023.9"
QIIME2_CHANNEL = "bioconda"
QIIME2_CHANNEL_PRIORITY = 1

# Required QIIME2 plugins/packages for this project
REQUIRED_PACKAGES = [
    "qiime2",
    "qiime2-plugins",
    "dada2",
    "deblur",
    "q2-demux",
    "q2-dada2",
    "q2-diversity",
    "q2-taxa",
    "q2-feature-table",
    "q2-types",
    "q2-metadata",
    "q2-longitudinal",
    "q2-composition",
    "q2-sample-classifier",
    "q2-emperor",
    "q2-gneiss",
    "q2-fragment-insertion",
    "q2-phylogeny",
    "q2-rescript",
    "q2-feature-classifier",
    "q2-fragment-insertion",
    "q2-phylogeny",
    "q2-taxa",
    "q2-composition",
    "q2-sample-classifier",
    "q2-longitudinal",
    "q2-emperor",
    "q2-gneiss",
    "q2-rescript",
    "q2-feature-classifier"
]

def check_conda_installed() -> bool:
    """Check if conda or mamba is installed."""
    try:
        subprocess.run(["conda", "--version"], check=True, capture_output=True)
        logger.info("Conda is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(["mamba", "--version"], check=True, capture_output=True)
            logger.info("Mamba is installed.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Neither conda nor mamba is installed. Please install one first.")
            return False

def create_qiime2_environment() -> bool:
    """
    Create the QIIME2 Conda environment if it doesn't exist.
    
    Returns:
        bool: True if environment was created successfully or already exists, False otherwise.
    """
    if not check_conda_installed():
        return False

    logger.info(f"Checking for QIIME2 environment: {QIIME2_ENV_NAME}...")
    
    # Check if environment exists
    try:
        result = subprocess.run(
            ["conda", "env", "list"],
            check=True,
            capture_output=True,
            text=True
        )
        if QIIME2_ENV_NAME in result.stdout:
            logger.info(f"QIIME2 environment '{QIIME2_ENV_NAME}' already exists.")
            return True
    except subprocess.CalledProcessError:
        logger.warning("Could not list conda environments. Attempting to create anyway.")

    logger.info(f"Creating QIIME2 environment '{QIIME2_ENV_NAME}'...")
    
    # Create environment with QIIME2
    # Using conda-forge and bioconda channels as recommended for QIIME2
    create_cmd = [
        "conda", "create", "-n", QIIME2_ENV_NAME, "-c", "conda-forge", "-c", "bioconda",
        f"qiime2={QIIME2_VERSION}", "python=3.10", "-y"
    ]
    
    try:
        subprocess.run(create_cmd, check=True)
        logger.info(f"Successfully created QIIME2 environment '{QIIME2_ENV_NAME}'.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create QIIME2 environment: {e}")
        logger.error("This might be due to channel conflicts or network issues.")
        logger.error("Please try creating the environment manually with:")
        logger.error(f"  conda create -n {QIIME2_ENV_NAME} -c conda-forge -c bioconda qiime2={QIIME2_VERSION} python=3.10 -y")
        return False

def activate_qiime2_environment() -> bool:
    """
    Activate the QIIME2 environment and verify it's active.
    
    Returns:
        bool: True if environment is active, False otherwise.
    """
    if not check_conda_installed():
        return False

    # Check if we're already in the environment
    if os.environ.get("CONDA_DEFAULT_ENV") == QIIME2_ENV_NAME:
        logger.info(f"Already in QIIME2 environment: {QIIME2_ENV_NAME}")
        return True

    logger.info(f"Attempting to activate QIIME2 environment: {QIIME2_ENV_NAME}...")
    
    # Try to activate and check if it worked
    try:
        # Use conda activate in a subprocess to verify
        activate_cmd = [
            "conda", "activate", QIIME2_ENV_NAME, "&&", "python", "-c", 
            "import qiime2; print('QIIME2 imported successfully')"
        ]
        
        # Note: This is a simplified check. In a real shell, we'd use eval "$(conda shell.bash hook)"
        # For this script, we'll just verify the environment exists and can be activated
        result = subprocess.run(
            ["conda", "run", "-n", QIIME2_ENV_NAME, "python", "-c", "import qiime2; print('OK')"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and "OK" in result.stdout:
            logger.info(f"QIIME2 environment '{QIIME2_ENV_NAME}' is ready.")
            return True
        else:
            logger.error(f"Failed to verify QIIME2 environment: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error checking QIIME2 environment: {e}")
        return False

def verify_qiime2_installation() -> Tuple[bool, str]:
    """
    Verify that QIIME2 is properly installed and all required plugins are available.
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not check_conda_installed():
        return False, "Conda/Mamba not found."

    if not activate_qiime2_environment():
        return False, "QIIME2 environment not active or not found."

    logger.info("Verifying QIIME2 installation...")
    
    # Check QIIME2 version
    try:
        result = subprocess.run(
            ["conda", "run", "-n", QIIME2_ENV_NAME, "qiime", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"QIIME2 version: {result.stdout.strip()}")
        else:
            return False, f"Failed to get QIIME2 version: {result.stderr}"
            
    except Exception as e:
        return False, f"Error checking QIIME2 version: {e}"

    # Check for required plugins
    missing_plugins = []
    for plugin in ["demux", "dada2", "diversity", "feature-table", "metadata"]:
        try:
            result = subprocess.run(
                ["conda", "run", "-n", QIIME2_ENV_NAME, "qiime", "plugin", "list"],
                capture_output=True,
                text=True
            )
            if plugin not in result.stdout:
                missing_plugins.append(plugin)
        except Exception as e:
            logger.warning(f"Could not check plugin {plugin}: {e}")
            missing_plugins.append(plugin)

    if missing_plugins:
        return False, f"Missing required plugins: {', '.join(missing_plugins)}"

    logger.info("All required QIIME2 components verified.")
    return True, "QIIME2 installation verified successfully."

def run_qiime2_command(command_args: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """
    Run a QIIME2 command within the correct conda environment.
    
    Args:
        command_args: List of arguments for the qiime command (e.g., ["demux", "summarize", ...])
        cwd: Working directory for the command
        
    Returns:
        CompletedProcess: The result of the subprocess run
    """
    if not check_conda_installed():
        raise RuntimeError("Conda/Mamba not found. Cannot run QIIME2 commands.")

    if not activate_qiime2_environment():
        raise RuntimeError("QIIME2 environment not active. Cannot run QIIME2 commands.")

    cmd = ["conda", "run", "-n", QIIME2_ENV_NAME, "qiime"] + command_args
    
    logger.info(f"Running QIIME2 command: {' '.join(cmd)}")
    
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=False,
        text=True
    )

def setup_qiime2_environment() -> bool:
    """
    Main setup function: ensures conda is available, creates the environment if needed,
    and verifies the installation.
    
    Returns:
        bool: True if setup was successful, False otherwise.
    """
    logger.info("Starting QIIME2 environment setup...")
    
    if not check_conda_installed():
        logger.error("Conda/Mamba is required but not installed.")
        logger.error("Please install Miniconda or Mambaforge from:")
        logger.error("  https://docs.conda.io/en/latest/miniconda.html")
        logger.error("  https://github.com/mamba-org/mamba#installation")
        return False

    if not create_qiime2_environment():
        logger.error("Failed to create QIIME2 environment.")
        return False

    if not activate_qiime2_environment():
        logger.error("Failed to activate QIIME2 environment.")
        return False

    success, message = verify_qiime2_installation()
    if not success:
        logger.error(f"QIIME2 verification failed: {message}")
        return False

    logger.info("QIIME2 environment setup complete!")
    logger.info(f"Environment name: {QIIME2_ENV_NAME}")
    logger.info("You can now run QIIME2 commands using:")
    logger.info(f"  conda activate {QIIME2_ENV_NAME}")
    logger.info("  qiime <command> [options]")
    
    return True

def main():
    """Main entry point for the QIIME2 setup script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Setup and configure QIIME2 Conda environment for microbiome analysis."
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing installation, do not create environment."
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Force recreation of the QIIME2 environment."
    )
    
    args = parser.parse_args()
    
    if args.verify_only:
        success, message = verify_qiime2_installation()
        if success:
            logger.info("QIIME2 verification successful.")
            sys.exit(0)
        else:
            logger.error(f"QIIME2 verification failed: {message}")
            sys.exit(1)
    
    # Default behavior: setup environment
    success = setup_qiime2_environment()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
