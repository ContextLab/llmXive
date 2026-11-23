import subprocess
import sys
import os
from pathlib import Path
import tomli_w
import tomli

from utils.logging import get_logger

logger = get_logger(__name__)


def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a shell command.
    
    Args:
        cmd: Command and arguments as a list.
        check: If True, raise CalledProcessError on non-zero exit.
        
    Returns:
        CompletedProcess instance.
    """
    logger.info(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result


def create_flake8_config() -> bool:
    """
    Create a .flake8 configuration file.
    
    Returns:
        True on success, False on failure.
    """
    config_content = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist
ignore = E203, E266, W503
max-complexity = 10
"""
    path = Path(".flake8")
    try:
        path.write_text(config_content)
        logger.info(f"Created {path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create .flake8: {e}")
        return False


def create_pyproject_toml() -> bool:
    """
    Create a pyproject.toml file with black configuration.
    
    Returns:
        True on success, False on failure.
    """
    config = {
        "tool": {
            "black": {
                "line-length": 88,
                "target-version": ["py39"],
                "include": "\\.pyi?$",
                "exclude": "/(\n    \\.git\n    | \\.hg\n    | \\.mypy_cache\n    | \\.tox\n    | \\.venv\n    | _build\n    | buck-out\n    | build\n    | dist\n)/\n"
            }
        }
    }
    
    path = Path("pyproject.toml")
    try:
        # Check if file exists and load existing config to avoid overwriting other sections
        existing_config = {}
        if path.exists():
            existing_content = path.read_text()
            try:
                existing_config = tomli.loads(existing_content)
            except tomli.TOMLDecodeError:
                logger.warning("Existing pyproject.toml is invalid TOML, overwriting.")
        
        # Merge black config
        if "tool" not in existing_config:
            existing_config["tool"] = {}
        existing_config["tool"]["black"] = config["tool"]["black"]
        
        with open(path, "wb") as f:
            tomli_w.dump(existing_config, f)
        
        logger.info(f"Updated {path} with black configuration")
        return True
    except OSError as e:
        logger.error(f"Failed to create/update pyproject.toml: {e}")
        return False


def install_dev_dependencies() -> bool:
    """
    Install development dependencies (flake8, black, pre-commit).
    
    Returns:
        True on success, False on failure.
    """
    deps = ["flake8", "black", "pre-commit"]
    try:
        run_command([sys.executable, "-m", "pip", "install", "-q"] + deps)
        logger.info("Development dependencies installed.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dev dependencies: {e}")
        return False


def setup_pre_commit() -> bool:
    """
    Initialize pre-commit hooks.
    
    Returns:
        True on success, False on failure.
    """
    try:
        run_command(["pre-commit", "install"], check=False)
        logger.info("Pre-commit installed.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install pre-commit: {e}")
        return False


def main() -> int:
    """
    Main entry point to set up linting and formatting tools.
    
    Returns:
        0 on success, 1 on failure.
    """
    logger.info("Setting up linting and formatting tools...")
    
    success = True
    success &= create_flake8_config()
    success &= create_pyproject_toml()
    success &= install_dev_dependencies()
    success &= setup_pre_commit()
    
    if success:
        logger.info("Linting setup completed successfully.")
        return 0
    else:
        logger.error("Linting setup encountered errors.")
        return 1


if __name__ == "__main__":
    sys.exit(main())