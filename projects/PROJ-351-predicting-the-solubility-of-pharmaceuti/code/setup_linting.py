import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Tuple, Optional

# Configure logging for setup operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_tool_installed(tool_name: str) -> Tuple[bool, str]:
    """
    Check if a linting/formatting tool is installed in the current environment.
    
    Args:
        tool_name: Name of the tool to check (e.g., 'flake8', 'black')
        
    Returns:
        Tuple of (is_installed, version_or_error_message)
    """
    try:
        result = subprocess.run(
            [tool_name, '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, f"Command failed with return code {result.returncode}"
    except FileNotFoundError:
        return False, f"Tool '{tool_name}' not found in PATH"
    except subprocess.TimeoutExpired:
        return False, f"Timeout checking '{tool_name}'"
    except Exception as e:
        return False, f"Error checking '{tool_name}': {str(e)}"

def create_flake8_config(project_root: Path) -> Path:
    """
    Create a .flake8 configuration file for the project.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Path to the created configuration file
    """
    config_path = project_root / '.flake8'
    
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info,
    data/raw,
    data/processed,
    models,
    results,
    .venv,
    venv,
    env
per-file-ignores =
    # Allow unused imports in __init__.py for exports
    */__init__.py: F401
    # Allow long lines in test files for readability
    tests/*: E501
"""
    
    try:
        with open(config_path, 'w') as f:
            f.write(config_content)
        logger.info(f"Created .flake8 configuration at {config_path}")
        return config_path
    except IOError as e:
        logger.error(f"Failed to create .flake8 config: {e}")
        raise

def create_black_config(project_root: Path) -> Path:
    """
    Create a pyproject.toml configuration file with Black settings.
    Note: We append to existing pyproject.toml if it exists, or create new.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Path to the configuration file
    """
    config_path = project_root / 'pyproject.toml'
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py310']
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
  | data/raw
  | data/processed
  | models
  | results
  | \.egg-info
)/
'''
"""

    try:
        # Check if pyproject.toml already exists
        if config_path.exists():
            with open(config_path, 'r') as f:
                existing_content = f.read()
            
            # Only add if [tool.black] section doesn't exist
            if '[tool.black]' not in existing_content:
                with open(config_path, 'a') as f:
                    f.write(black_section)
                logger.info(f"Appended [tool.black] section to {config_path}")
            else:
                logger.info(f"[tool.black] section already exists in {config_path}")
        else:
            with open(config_path, 'w') as f:
                f.write(black_section.strip() + '\n')
            logger.info(f"Created pyproject.toml with [tool.black] section at {config_path}")
        
        return config_path
    except IOError as e:
        logger.error(f"Failed to create/update pyproject.toml: {e}")
        raise

def main() -> int:
    """
    Main entry point for setting up linting and formatting tools.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Starting linting and formatting setup...")
    
    # Determine project root (parent of code directory)
    current_path = Path(__file__).resolve()
    project_root = current_path.parent.parent
    
    logger.info(f"Project root: {project_root}")
    
    # Check for flake8
    is_installed, message = check_tool_installed('flake8')
    if is_installed:
        logger.info(f"✓ flake8 is installed: {message}")
    else:
        logger.warning(f"✗ flake8 is not installed: {message}")
        logger.info("Install with: pip install flake8")
    
    # Check for black
    is_installed, message = check_tool_installed('black')
    if is_installed:
        logger.info(f"✓ black is installed: {message}")
    else:
        logger.warning(f"✗ black is not installed: {message}")
        logger.info("Install with: pip install black")
    
    # Create configuration files
    try:
        flake8_config = create_flake8_config(project_root)
        black_config = create_black_config(project_root)
        
        logger.info("\nConfiguration files created successfully:")
        logger.info(f"  - {flake8_config}")
        logger.info(f"  - {black_config}")
        
        logger.info("\nTo run linting: flake8 code/ tests/")
        logger.info("To run formatting: black code/ tests/")
        
        return 0
    except Exception as e:
        logger.error(f"Failed to create configuration files: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())