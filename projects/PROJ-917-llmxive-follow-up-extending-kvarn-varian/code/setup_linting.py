"""
Linting and Formatting Configuration Setup for llmXive.

This module configures ruff (linting) and black (formatting) tools
for the project. It creates necessary configuration files and provides
verification utilities.
"""

import subprocess
import sys
from pathlib import Path
import os
import tomli_w
import tomli
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_tool(tool_name: str) -> bool:
    """
    Check if a tool is installed and available.

    Args:
        tool_name: Name of the tool to check (e.g., 'ruff', 'black')

    Returns:
        True if the tool is available, False otherwise.
    """
    try:
        result = subprocess.run(
            [tool_name, '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            logger.info(f"{tool_name} is installed: {result.stdout.strip()}")
            return True
        else:
            logger.warning(f"{tool_name} is not available or not installed.")
            return False
    except FileNotFoundError:
        logger.warning(f"{tool_name} not found in PATH.")
        return False
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout checking {tool_name}.")
        return False

def install_tools() -> bool:
    """
    Install ruff and black if not already installed.

    Returns:
        True if installation was successful, False otherwise.
    """
    tools = ['ruff', 'black']
    success = True

    for tool in tools:
        if not check_tool(tool):
            logger.info(f"Installing {tool}...")
            try:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', tool],
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info(f"{tool} installed successfully.")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {tool}: {e.stderr}")
                success = False

    return success

def create_ruff_config(project_root: Path) -> Path:
    """
    Create ruff configuration file (pyproject.toml).

    Args:
        project_root: Path to the project root directory.

    Returns:
        Path to the created configuration file.
    """
    config_path = project_root / 'pyproject.toml'
    
    # Default ruff configuration
    ruff_config = {
        'tool': {
            'ruff': {
                'target-version': 'py311',
                'line-length': 88,
                'select': [
                    'E',    # pycodestyle errors
                    'W',    # pycodestyle warnings
                    'F',    # Pyflakes
                    'I',    # isort
                    'C',    # flake8-comprehensions
                    'B',    # flake8-bugbear
                    'UP',   # pyupgrade
                ],
                'ignore': [
                    'E501',  # Line too long (handled by black)
                    'B008',  # Do not perform function call in argument defaults
                ],
                'exclude': [
                    '.git',
                    '__pycache__',
                    '.venv',
                    'venv',
                    'env',
                    '.eggs',
                    '*.egg-info',
                    'build',
                    'dist',
                ],
                'per-file-ignores': {
                    '__init__.py': ['F401'],  # Ignore unused imports in __init__.py
                },
            }
        }
    }

    # Check if file exists and load existing config
    existing_config = {}
    if config_path.exists():
        try:
            with open(config_path, 'rb') as f:
                existing_config = tomli.load(f)
        except Exception as e:
            logger.warning(f"Could not load existing pyproject.toml: {e}")
            # Start fresh if we can't read existing config

    # Merge configurations
    if 'tool' not in existing_config:
        existing_config['tool'] = {}
    existing_config['tool'].update(ruff_config['tool'])

    # Write merged configuration
    with open(config_path, 'wb') as f:
        tomli_w.dump(existing_config, f)

    logger.info(f"Ruff configuration created at {config_path}")
    return config_path

def create_black_config(project_root: Path) -> Path:
    """
    Create black configuration file (pyproject.toml).

    Args:
        project_root: Path to the project root directory.

    Returns:
        Path to the created configuration file.
    """
    config_path = project_root / 'pyproject.toml'
    
    # Default black configuration
    black_config = {
        'tool': {
            'black': {
                'line-length': 88,
                'target-version': ['py311'],
                'exclude': r'''
                    (
                        \.git
                        | __pycache__
                        | \.venv
                        | venv
                        | env
                        | \.eggs
                        | .*\.egg-info
                        | build
                        | dist
                    )
                ''',
            }
        }
    }

    # Check if file exists and load existing config
    existing_config = {}
    if config_path.exists():
        try:
            with open(config_path, 'rb') as f:
                existing_config = tomli.load(f)
        except Exception as e:
            logger.warning(f"Could not load existing pyproject.toml: {e}")

    # Merge configurations
    if 'tool' not in existing_config:
        existing_config['tool'] = {}
    existing_config['tool'].update(black_config['tool'])

    # Write merged configuration
    with open(config_path, 'wb') as f:
        tomli_w.dump(existing_config, f)

    logger.info(f"Black configuration created at {config_path}")
    return config_path

def verify_setup(project_root: Path) -> dict:
    """
    Verify that linting and formatting tools are properly configured.

    Args:
        project_root: Path to the project root directory.

    Returns:
        Dictionary with verification results.
    """
    results = {
        'ruff_installed': False,
        'black_installed': False,
        'ruff_config_exists': False,
        'black_config_exists': False,
        'config_path': None,
        'errors': []
    }

    # Check tool installation
    results['ruff_installed'] = check_tool('ruff')
    results['black_installed'] = check_tool('black')

    # Check configuration file
    config_path = project_root / 'pyproject.toml'
    results['config_path'] = str(config_path)

    if config_path.exists():
        try:
            with open(config_path, 'rb') as f:
                config = tomli.load(f)
            
            results['ruff_config_exists'] = 'ruff' in config.get('tool', {})
            results['black_config_exists'] = 'black' in config.get('tool', {})
            
            if results['ruff_config_exists']:
                logger.info("Ruff configuration found in pyproject.toml")
            if results['black_config_exists']:
                logger.info("Black configuration found in pyproject.toml")
                
        except Exception as e:
            results['errors'].append(f"Error reading config: {e}")
    else:
        results['errors'].append("pyproject.toml not found")

    return results

def main():
    """
    Main entry point for linting setup.
    """
    logger.info("Starting linting and formatting setup...")
    
    # Determine project root (parent of code/)
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    
    # Install tools if needed
    if not install_tools():
        logger.error("Failed to install required tools. Aborting.")
        sys.exit(1)

    # Create configuration files
    logger.info("Creating configuration files...")
    create_ruff_config(project_root)
    create_black_config(project_root)

    # Verify setup
    logger.info("Verifying setup...")
    results = verify_setup(project_root)

    # Report results
    logger.info("=" * 50)
    logger.info("Setup Results:")
    logger.info(f"  Ruff installed: {results['ruff_installed']}")
    logger.info(f"  Black installed: {results['black_installed']}")
    logger.info(f"  Ruff config exists: {results['ruff_config_exists']}")
    logger.info(f"  Black config exists: {results['black_config_exists']}")
    
    if results['errors']:
        logger.warning("Errors encountered:")
        for error in results['errors']:
            logger.warning(f"  - {error}")
    else:
        logger.info("Setup completed successfully!")

    # Summary
    all_good = (
        results['ruff_installed'] and 
        results['black_installed'] and 
        results['ruff_config_exists'] and 
        results['black_config_exists']
    )

    if all_good:
        logger.info("All linting and formatting tools are ready to use.")
        logger.info("Run 'ruff check .' to check for linting issues.")
        logger.info("Run 'black .' to format code.")
    else:
        logger.warning("Setup completed with warnings. Please review the output above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
