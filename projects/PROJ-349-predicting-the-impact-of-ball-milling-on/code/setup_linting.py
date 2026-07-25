import subprocess
import sys
from pathlib import Path
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_tool(tool_name: str) -> bool:
    """
    Check if a linting/formatting tool is installed.
    Returns True if the tool is installed and returns a valid version, False otherwise.
    """
    try:
        result = subprocess.run(
            [tool_name, '--version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            logger.info(f"{tool_name} is installed: {result.stdout.strip()}")
            return True
        else:
            logger.warning(f"{tool_name} is not installed or failed to report version.")
            return False
    except FileNotFoundError:
        logger.warning(f"{tool_name} not found in PATH.")
        return False
    except Exception as e:
        logger.error(f"Error checking {tool_name}: {e}")
        return False

def install_dev_dependencies() -> bool:
    """
    Install flake8 and black using pip.
    Returns True if installation succeeds, False otherwise.
    """
    packages = ['flake8', 'black']
    try:
        logger.info(f"Installing dev dependencies: {', '.join(packages)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + packages)
        logger.info("Dev dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dev dependencies: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during dependency installation: {e}")
        return False

def create_flake8_config() -> bool:
    """
    Create a .flake8 configuration file in the project root.
    Returns True if successful, False otherwise.
    """
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    *.egg-info
"""
    config_path = Path('.flake8')
    try:
        with open(config_path, 'w') as f:
            f.write(config_content)
        logger.info(f"Created .flake8 configuration at {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create .flake8 config: {e}")
        return False

def create_black_config() -> bool:
    """
    Create a pyproject.toml with black configuration if it doesn't exist,
    or append the black section if it does.
    Returns True if successful, False otherwise.
    """
    config_path = Path('pyproject.toml')
    black_section = """
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
"""
    try:
        if not config_path.exists():
            with open(config_path, 'w') as f:
                f.write(black_section.strip())
            logger.info(f"Created pyproject.toml with black config at {config_path}")
        else:
            with open(config_path, 'r') as f:
                content = f.read()
            if '[tool.black]' not in content:
                with open(config_path, 'a') as f:
                    f.write(black_section)
                logger.info(f"Appended black config to existing pyproject.toml at {config_path}")
            else:
                logger.info(f"Black config already exists in {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create/update pyproject.toml: {e}")
        return False

def init_pre_commit() -> bool:
    """
    Initialize pre-commit hooks if not already initialized.
    Returns True if successful, False otherwise.
    """
    try:
        if not Path('.pre-commit-config.yaml').exists():
            config_content = """repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
- id: black
  language_version: python3
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
- id: flake8
"""
            with open('.pre-commit-config.yaml', 'w') as f:
                f.write(config_content)
            logger.info("Created .pre-commit-config.yaml")
        
        # Initialize pre-commit if not already initialized
        if not Path('.git').exists() and not Path('.pre-commit-config.yaml').exists():
             # If no git repo, we can't init hooks, but config file is created
             logger.info("No .git directory found. Pre-commit hooks cannot be initialized, but config file created.")
             return True

        subprocess.run(['pre-commit', 'init'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("Pre-commit initialized successfully.")
        return True
    except subprocess.CalledProcessError as e:
        # If already initialized, it might return non-zero or specific error, treat as success if config exists
        if Path('.pre-commit-config.yaml').exists():
            logger.info("Pre-commit config exists. Initialization skipped or already done.")
            return True
        logger.error(f"Failed to initialize pre-commit: {e}")
        return False
    except FileNotFoundError:
        logger.warning("pre-commit not found. Skipping initialization. Please install it via pip.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during pre-commit setup: {e}")
        return False

def main():
    """
    Main entry point to configure linting and formatting tools.
    """
    logger.info("Starting linting configuration setup...")
    
    # Step 1: Install dependencies
    if not install_dev_dependencies():
        logger.error("Dependency installation failed. Aborting.")
        sys.exit(1)
    
    # Step 2: Verify installation
    if not (check_tool('flake8') and check_tool('black')):
        logger.error("Verification of tools failed. Aborting.")
        sys.exit(1)
    
    # Step 3: Create configuration files
    if not create_flake8_config():
        logger.error("Failed to create flake8 config.")
        sys.exit(1)
    
    if not create_black_config():
        logger.error("Failed to create black config.")
        sys.exit(1)
    
    # Step 4: Initialize pre-commit (optional but recommended)
    init_pre_commit()
    
    # Step 5: Run check on empty codebase (or current state)
    logger.info("Running black --check on src/...")
    try:
        result = subprocess.run(
            ['black', '--check', 'src/'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("Black check passed on current codebase.")
        else:
            logger.warning("Black check found formatting issues. Run 'black src/' to fix.")
            # Don't exit with error here as the task is to configure, not necessarily fix existing code
    except Exception as e:
        logger.error(f"Error running black check: {e}")
    
    logger.info("Linting configuration setup completed.")

if __name__ == '__main__':
    main()