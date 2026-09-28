import os
import sys
import subprocess
from pathlib import Path
import toml
import logging
from typing import List, Dict, Any, Optional

# Configure logging to match project standards
def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "setup.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists at the given path."""
    path = Path(file_path)
    exists = path.exists()
    if exists:
        logger.info(f"Found: {file_path}")
    else:
        logger.warning(f"Missing: {file_path}")
    return exists

def validate_pyproject_config() -> bool:
    """Validate or create pyproject.toml with black and isort configurations."""
    pyproject_path = Path("pyproject.toml")
    
    if pyproject_path.exists():
        logger.info("pyproject.toml exists. Checking configuration...")
        try:
            with open(pyproject_path, "r") as f:
                config = toml.load(f)
            
            tool_config = config.get("tool", {})
            has_black = "black" in tool_config
            has_isort = "isort" in tool_config
            
            if not has_black:
                logger.warning("Black configuration missing in pyproject.toml. Adding it.")
                return False
            if not has_isort:
                logger.warning("isort configuration missing in pyproject.toml. Adding it.")
                return False
            
            logger.info("pyproject.toml has valid Black and isort configurations.")
            return True
        except Exception as e:
            logger.error(f"Error reading pyproject.toml: {e}")
            return False
    else:
        logger.info("pyproject.toml not found. Creating with default configurations...")
        try:
            config_content = """
[tool.black]
line-length = 88
target-version = ['py38']
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

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
"""
            with open(pyproject_path, "w") as f:
                f.write(config_content.strip())
            logger.info(f"Created {pyproject_path} with Black and isort configurations.")
            return True
        except Exception as e:
            logger.error(f"Error creating pyproject.toml: {e}")
            return False

def validate_flake8_config() -> bool:
    """Validate or create .flake8 configuration file."""
    flake8_path = Path(".flake8")
    
    if flake8_path.exists():
        logger.info(".flake8 exists. Validating content...")
        try:
            with open(flake8_path, "r") as f:
                content = f.read()
            
            required_sections = ["[flake8]"]
            missing = [s for s in required_sections if s not in content]
            
            if missing:
                logger.warning(f".flake8 is missing required sections: {missing}")
                return False
            
            # Check for essential ignores
            if "ignore =" not in content:
                logger.warning(".flake8 missing 'ignore' setting. Adding defaults.")
                return False
            
            logger.info(".flake8 configuration is valid.")
            return True
        except Exception as e:
            logger.error(f"Error reading .flake8: {e}")
            return False
    else:
        logger.info(".flake8 not found. Creating with default configuration...")
        try:
            config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .venv,
    venv,
    *.egg-info
per-file-ignores =
    # Allow unused imports in __init__.py
    */__init__.py: F401
"""
            with open(flake8_path, "w") as f:
                f.write(config_content)
            logger.info(f"Created {flake8_path} with default flake8 configuration.")
            return True
        except Exception as e:
            logger.error(f"Error creating .flake8: {e}")
            return False

def validate_precommit_config() -> bool:
    """Validate or create .pre-commit-config.yaml."""
    precommit_path = Path(".pre-commit-config.yaml")
    
    if precommit_path.exists():
        logger.info(".pre-commit-config.yaml exists. Validating content...")
        try:
            with open(precommit_path, "r") as f:
                content = f.read()
            
            required_hooks = ["black", "flake8", "isort"]
            missing = [h for h in required_hooks if h not in content]
            
            if missing:
                logger.warning(f".pre-commit-config.yaml is missing hooks: {missing}")
                return False
            
            logger.info(".pre-commit-config.yaml is valid.")
            return True
        except Exception as e:
            logger.error(f"Error reading .pre-commit-config.yaml: {e}")
            return False
    else:
        logger.info(".pre-commit-config.yaml not found. Creating with default configuration...")
        try:
            config_content = """repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
- id: black
  language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
- id: flake8

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
- id: isort
  args: ["--profile", "black"]
"""
            with open(precommit_path, "w") as f:
                f.write(config_content)
            logger.info(f"Created {precommit_path} with default pre-commit configuration.")
            return True
        except Exception as e:
            logger.error(f"Error creating .pre-commit-config.yaml: {e}")
            return False

def install_requirements() -> bool:
    """Install linting and formatting tools if not already installed."""
    tools = [
        ("black", "black"),
        ("flake8", "flake8"),
        ("isort", "isort"),
        ("pre-commit", "pre-commit")
    ]
    
    missing_tools = []
    for pkg, cmd in tools:
        try:
            subprocess.run([sys.executable, "-m", "pip", "show", pkg], 
                         capture_output=True, check=True)
            logger.info(f"{pkg} is already installed.")
        except subprocess.CalledProcessError:
            missing_tools.append(pkg)
            logger.warning(f"{pkg} is not installed.")
    
    if missing_tools:
        logger.info(f"Installing missing tools: {', '.join(missing_tools)}")
        try:
            # Install from requirements.txt if it exists, otherwise install directly
            requirements_path = Path("code/requirements.txt")
            if requirements_path.exists():
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)], 
                             check=True)
            else:
                subprocess.run([sys.executable, "-m", "pip", "install"] + missing_tools, 
                             check=True)
            logger.info("Successfully installed missing tools.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install tools: {e}")
            return False
    
    return True

def run_linting() -> bool:
    """Run flake8 on the code directory."""
    code_dir = Path("code")
    if not code_dir.exists():
        logger.error("code/ directory does not exist.")
        return False
    
    try:
        result = subprocess.run(
            ["flake8", str(code_dir)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Flake8 linting passed with no issues.")
            return True
        else:
            logger.warning(f"Flake8 found issues:\n{result.stdout}")
            return False
    except FileNotFoundError:
        logger.error("flake8 is not installed or not in PATH.")
        return False
    except Exception as e:
        logger.error(f"Error running flake8: {e}")
        return False

def run_formatting() -> bool:
    """Run black on the code directory."""
    code_dir = Path("code")
    if not code_dir.exists():
        logger.error("code/ directory does not exist.")
        return False
    
    try:
        result = subprocess.run(
            ["black", "--check", str(code_dir)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Black formatting check passed.")
            return True
        else:
            logger.warning(f"Black formatting issues found:\n{result.stdout}")
            return False
    except FileNotFoundError:
        logger.error("black is not installed or not in PATH.")
        return False
    except Exception as e:
        logger.error(f"Error running black: {e}")
        return False

def main():
    """Main entry point for linting setup."""
    logger.info("Starting linting and formatting configuration setup...")
    
    success = True
    
    # Install tools
    if not install_requirements():
        success = False
    
    # Create/validate configuration files
    if not validate_pyproject_config():
        success = False
    
    if not validate_flake8_config():
        success = False
    
    if not validate_precommit_config():
        success = False
    
    # Run checks if everything is set up
    if success:
        logger.info("Configuration files validated. Running linting and formatting checks...")
        if not run_linting():
            logger.warning("Linting check failed. Please fix issues.")
        
        if not run_formatting():
            logger.warning("Formatting check failed. Please run 'black code/' to fix.")
    
    if success:
        logger.info("Linting and formatting setup completed successfully.")
        return 0
    else:
        logger.error("Linting and formatting setup completed with errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())