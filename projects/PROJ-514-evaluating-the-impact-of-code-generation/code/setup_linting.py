import os
import sys
import subprocess
from pathlib import Path
import logging
from utils.logger import get_logger

def ensure_requirements():
    """Install ruff and black if not present."""
    logger = get_logger(__name__)
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ruff==0.1.6", "black"])
        logger.info("Dependencies ruff and black installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        sys.exit(1)

def create_ruff_config(config_path: Path):
    """Create ruff configuration in pyproject.toml."""
    logger = get_logger(__name__)
    # The configuration is already defined in pyproject.toml directly per task spec,
    # but we ensure the file exists and contains the correct block.
    if not config_path.exists():
        logger.warning(f"Config file {config_path} does not exist. Creating it.")
        # This file is created by the artifact, so we just verify it here if needed.
        return

    # Verify content matches spec
    content = config_path.read_text()
    required_sections = ["[tool.ruff]", "select =", "line-length = 100"]
    for section in required_sections:
        if section not in content:
            logger.error(f"Missing required section '{section}' in pyproject.toml")
            sys.exit(1)
    
    logger.info("Ruff configuration verified in pyproject.toml.")

def create_black_config(config_path: Path):
    """Create black configuration in pyproject.toml."""
    logger = get_logger(__name__)
    if not config_path.exists():
        logger.warning(f"Config file {config_path} does not exist.")
        return

    content = config_path.read_text()
    required_sections = ["[tool.black]", "line-length = 100"]
    for section in required_sections:
        if section not in content:
            logger.error(f"Missing required section '{section}' in pyproject.toml")
            sys.exit(1)

    logger.info("Black configuration verified in pyproject.toml.")

def main():
    logger = get_logger(__name__)
    project_root = Path(__file__).resolve().parent
    pyproject_path = project_root / "pyproject.toml"

    # Ensure requirements are installed
    ensure_requirements()

    # Create/Verify config files
    # Note: The pyproject.toml content is provided as an artifact in this task.
    # This script verifies the configuration is correct and linting tools are available.
    if not pyproject_path.exists():
        logger.error("pyproject.toml not found. Ensure the artifact was created.")
        sys.exit(1)

    create_ruff_config(pyproject_path)
    create_black_config(pyproject_path)

    # Run a dry-run check to ensure ruff can parse the config
    try:
        result = subprocess.run(
            ["ruff", "check", "--config", str(pyproject_path), "--output-format=concise", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        # Ruff returns 0 if no issues, 1 if issues found. We just want to ensure it runs without config error.
        if result.returncode not in [0, 1]:
            logger.error(f"Ruff check failed with unexpected exit code {result.returncode}: {result.stderr}")
            sys.exit(1)
        logger.info("Ruff configuration is valid and executable.")
    except subprocess.TimeoutExpired:
        logger.error("Ruff check timed out.")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("Ruff executable not found. Ensure it was installed.")
        sys.exit(1)

if __name__ == "__main__":
    main()