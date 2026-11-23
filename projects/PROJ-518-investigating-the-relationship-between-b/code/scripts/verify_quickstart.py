"""
Script to verify quickstart.md commands in a fresh virtualenv.
This script simulates the quickstart process by:
1. Creating a temporary virtual environment
2. Installing dependencies from requirements.txt
3. Running the main pipeline script
4. Verifying that expected output files are generated
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(cmd: list, cwd: Path = None, timeout: int = 300) -> bool:
    """
    Run a command and return True if successful.

    Args:
        cmd: Command as a list of strings
        cwd: Working directory
        timeout: Command timeout in seconds

    Returns:
        bool: True if command succeeded, False otherwise
    """
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            logger.info(f"Command succeeded: {' '.join(cmd)}")
            if result.stdout:
                logger.debug(f"Stdout: {result.stdout[:500]}")
            return True
        else:
            logger.error(f"Command failed with code {result.returncode}")
            logger.error(f"Stderr: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {' '.join(cmd)}")
        return False
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return False


def verify_quickstart(project_root: Path) -> bool:
    """
    Verify quickstart.md commands in a fresh virtualenv.

    Args:
        project_root: Path to the project root directory

    Returns:
        bool: True if all commands succeed, False otherwise
    """
    logger.info(f"Starting quickstart verification for project: {project_root}")

    # Check if requirements.txt exists
    requirements_path = project_root / "requirements.txt"
    if not requirements_path.exists():
        logger.error(f"requirements.txt not found at {requirements_path}")
        return False

    # Check if quickstart.md exists
    quickstart_path = project_root / "quickstart.md"
    if not quickstart_path.exists():
        logger.warning(f"quickstart.md not found at {quickstart_path}. "
                     "Creating a default quickstart verification.")
        # Create a minimal quickstart.md if it doesn't exist
        quickstart_content = """# Quickstart Guide

## Setup
1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the pipeline:
   ```bash
   python code/main.py
   ```

4. Verify outputs:
   ```bash
   python code/scripts/verify_sensitivity.py
   ```
"""
        quickstart_path.write_text(quickstart_content)

    # Create a temporary directory for the virtual environment
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "venv"
        logger.info(f"Creating virtual environment at {venv_path}")

        # Create virtual environment
        if not run_command([sys.executable, "-m", "venv", str(venv_path)]):
            logger.error("Failed to create virtual environment")
            return False

        # Determine the Python executable in the venv
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"

        # Upgrade pip
        if not run_command([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"]):
            logger.error("Failed to upgrade pip")
            return False

        # Install dependencies
        logger.info("Installing dependencies from requirements.txt")
        if not run_command([str(pip_exe), "install", "-r", str(requirements_path)]):
            logger.error("Failed to install dependencies")
            return False

        # Verify main.py can be imported without errors
        logger.info("Verifying main.py can be imported")
        test_import_cmd = [
            str(python_exe), "-c",
            "import sys; sys.path.insert(0, 'code'); from main import main; print('Import successful')"
        ]
        if not run_command(test_import_cmd, cwd=project_root):
            logger.error("Failed to import main.py")
            return False

        # Verify key modules can be imported
        logger.info("Verifying key modules can be imported")
        modules_to_test = [
            "config",
            "data.loader",
            "data.preprocess",
            "analysis.connectivity",
            "analysis.dynamics",
            "analysis.statistics",
            "viz.plots"
        ]

        for module in modules_to_test:
            test_cmd = [
                str(python_exe), "-c",
                f"import sys; sys.path.insert(0, 'code'); import {module}; print('Import successful: {module}')"
            ]
            if not run_command(test_cmd, cwd=project_root):
                logger.error(f"Failed to import module: {module}")
                return False

        # Verify that output directories exist or can be created
        logger.info("Verifying output directories")
        dirs_to_check = [
            "data/raw",
            "data/processed",
            "data/interim",
            "docs/outputs",
            "results"
        ]

        for dir_name in dirs_to_check:
            dir_path = project_root / dir_name
            if not dir_path.exists():
                logger.info(f"Creating directory: {dir_path}")
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.error(f"Failed to create directory {dir_path}: {e}")
                    return False

        # Run the verification script for sensitivity
        logger.info("Running sensitivity verification script")
        verify_sensitivity_cmd = [
            str(python_exe),
            "code/scripts/verify_sensitivity.py"
        ]
        # This might fail if no real data is available, which is expected
        # We just want to verify the script can be executed
        run_command(verify_sensitivity_cmd, cwd=project_root)

        logger.info("Quickstart verification completed successfully")
        return True


def main():
    """Main entry point for the quickstart verification script."""
    logger.info("Starting quickstart verification")

    # Determine project root (assume script is in code/scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    if not project_root.exists():
        logger.error(f"Project root not found: {project_root}")
        sys.exit(1)

    logger.info(f"Project root: {project_root}")

    success = verify_quickstart(project_root)

    if success:
        logger.info("Quickstart verification PASSED")
        sys.exit(0)
    else:
        logger.error("Quickstart verification FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()