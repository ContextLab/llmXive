import os
import subprocess
import sys
from pathlib import Path

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def install_tools():
    """Install ruff and black into the current environment."""
    logger.info("Installing linting and formatting tools (ruff, black)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
        logger.info("Tools installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install tools: {e}")
        return False

def create_ruff_config():
    """Create a .ruff.toml configuration file at the project root."""
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / ".ruff.toml"
    
    content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Created ruff config at: {config_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to create ruff config: {e}")
        return False

def create_black_config():
    """Create a pyproject.toml file with black configuration if it doesn't exist, 
    or append to it if it does."""
    project_root = Path(__file__).resolve().parent.parent
    config_path = project_root / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
"""
    
    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
            if "[tool.black]" not in existing_content:
                with open(config_path, "a", encoding="utf-8") as f:
                    f.write(black_section)
                logger.info(f"Appended black config to existing: {config_path}")
            else:
                logger.info(f"Black config already exists in: {config_path}")
        else:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(black_section)
            logger.info(f"Created new pyproject.toml with black config at: {config_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to create/append black config: {e}")
        return False

def verify_tools():
    """Verify that ruff and black are installed and accessible."""
    logger.info("Verifying tool installation...")
    tools = {
        "ruff": ["ruff", "--version"],
        "black": ["black", "--version"]
    }
    
    all_ok = True
    for name, cmd in tools.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"{name}: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            logger.error(f"{name} is not installed or not found in PATH.")
            all_ok = False
        except FileNotFoundError:
            logger.error(f"{name} command not found.")
            all_ok = False
    
    return all_ok

def main():
    """Main entry point for configuring linting and formatting tools."""
    logger.info("Starting linting and formatting configuration...")
    
    if not install_tools():
        logger.error("Installation failed. Aborting.")
        sys.exit(1)
    
    if not verify_tools():
        logger.error("Verification failed after installation. Aborting.")
        sys.exit(1)
    
    if not create_ruff_config():
        logger.error("Ruff config creation failed.")
        sys.exit(1)
    
    if not create_black_config():
        logger.error("Black config creation failed.")
        sys.exit(1)
    
    logger.info("Linting and formatting configuration complete.")

if __name__ == "__main__":
    main()