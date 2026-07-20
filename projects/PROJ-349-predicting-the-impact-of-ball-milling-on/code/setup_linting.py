"""
Script to configure and install linting and formatting tools for the project.
Handles installation of dev dependencies, configuration file creation, and
pre-commit initialization.
"""
import subprocess
import sys
from pathlib import Path
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_tool(tool_name: str) -> bool:
    """
    Check if a specific tool is installed and return its version.
    
    Args:
        tool_name: Name of the tool to check (e.g., 'flake8', 'black')
        
    Returns:
        True if the tool is installed, False otherwise.
    """
    try:
        result = subprocess.run(
            [tool_name, '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"{tool_name} is installed: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        logger.warning(f"{tool_name} is not installed or not in PATH.")
        return False
    except FileNotFoundError:
        logger.warning(f"{tool_name} command not found.")
        return False

def install_dev_dependencies() -> bool:
    """
    Install development dependencies from requirements-dev.txt.
    
    Returns:
        True if installation succeeds, False otherwise.
    """
    requirements_file = Path("requirements-dev.txt")
    if not requirements_file.exists():
        logger.error(f"Requirements file not found: {requirements_file}")
        return False

    logger.info(f"Installing development dependencies from {requirements_file}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True
        )
        logger.info("Development dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def create_flake8_config() -> bool:
    """
    Create a .flake8 configuration file if it doesn't exist.
    
    Returns:
        True if config is created or already exists, False on error.
    """
    config_path = Path(".flake8")
    if config_path.exists():
        logger.info(f"Configuration file {config_path} already exists.")
        return True

    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, E501, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
per-file-ignores =
    */__init__.py:F401
"""
    try:
        config_path.write_text(config_content)
        logger.info(f"Created {config_path} with default settings.")
        return True
    except IOError as e:
        logger.error(f"Failed to create {config_path}: {e}")
        return False

def create_black_config() -> bool:
    """
    Ensure black configuration exists in pyproject.toml.
    
    Returns:
        True if config is updated or already exists, False on error.
    """
    pyproject_path = Path("pyproject.toml")
    
    if not pyproject_path.exists():
        logger.warning(f"{pyproject_path} not found. Creating with black config...")
        content = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
    | \\.hg
    | \\.mypy_cache
    | \\.tox
    | \\.venv
    | _build
    | buck-out
    | build
    | dist
)/
'''
"""
        try:
            pyproject_path.write_text(content)
            logger.info(f"Created {pyproject_path} with black configuration.")
            return True
        except IOError as e:
            logger.error(f"Failed to create {pyproject_path}: {e}")
            return False

    # Check if black section exists
    content = pyproject_path.read_text()
    if "[tool.black]" in content:
        logger.info(f"Black configuration already exists in {pyproject_path}.")
        return True

    # Append black config
    black_config = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
    | \\.hg
    | \\.mypy_cache
    | \\.tox
    | \\.venv
    | _build
    | buck-out
    | build
    | dist
)/
'''
"""
    try:
        with open(pyproject_path, 'a') as f:
            f.write(black_config)
        logger.info(f"Added black configuration to {pyproject_path}.")
        return True
    except IOError as e:
        logger.error(f"Failed to update {pyproject_path}: {e}")
        return False

def init_pre_commit() -> bool:
    """
    Initialize pre-commit hooks if not already initialized.
    
    Returns:
        True if successful, False otherwise.
    """
    pre_commit_config = Path(".pre-commit-config.yaml")
    if not pre_commit_config.exists():
        logger.warning(f"{pre_commit_config} not found. Skipping pre-commit init.")
        return False

    logger.info("Initializing pre-commit hooks...")
    try:
        # Check if .git/hooks/pre-commit exists
        hook_path = Path(".git/hooks/pre-commit")
        if not hook_path.exists():
            subprocess.run(["pre-commit", "install"], check=True)
            logger.info("Pre-commit hooks installed.")
        else:
            logger.info("Pre-commit hooks already installed.")
        
        # Run a dry-run check
        subprocess.run(["pre-commit", "run", "--all-files"], check=False)
        return True
    except subprocess.CalledProcessError as e:
        logger.warning(f"Pre-commit setup or run had issues: {e}")
        return False
    except FileNotFoundError:
        logger.error("pre-commit command not found. Please install it first.")
        return False

def main():
    """Main entry point for the linting setup script."""
    logger.info("Starting linting and formatting configuration...")
    
    # 1. Install dependencies
    if not install_dev_dependencies():
        logger.error("Dependency installation failed. Aborting.")
        sys.exit(1)
    
    # 2. Verify tools
    tools = ["flake8", "black", "isort"]
    all_installed = True
    for tool in tools:
        if not check_tool(tool):
            all_installed = False
    
    if not all_installed:
        logger.error("One or more tools are missing after installation.")
        sys.exit(1)
    
    # 3. Create configuration files
    create_flake8_config()
    create_black_config()
    
    # 4. Initialize pre-commit
    init_pre_commit()
    
    # 5. Final check
    logger.info("Running black --check on codebase...")
    try:
        subprocess.run(["black", "--check", "code/"], check=True)
        logger.info("Code formatting check passed.")
    except subprocess.CalledProcessError:
        logger.warning("Code formatting check failed. Run 'black code/' to fix.")
    
    logger.info("Linting and formatting configuration complete.")

if __name__ == "__main__":
    main()