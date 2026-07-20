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
    Check if a linting/formatting tool is installed and return its version.
    
    Args:
        tool_name: Name of the tool (e.g., 'flake8', 'black')
        
    Returns:
        bool: True if tool is installed, False otherwise
    """
    try:
        result = subprocess.run(
            [tool_name, '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"{tool_name} version: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"{tool_name} not installed or error occurred: {e}")
        return False
    except FileNotFoundError:
        logger.error(f"{tool_name} command not found. Is it installed?")
        return False

def install_dev_dependencies() -> None:
    """Install linting and formatting dependencies."""
    logger.info("Installing development dependencies (flake8, black, pre-commit)...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "flake8",
            "black",
            "pre-commit"
        ])
        logger.info("Development dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        raise

def create_flake8_config(root_dir: Path) -> None:
    """
    Create a .flake8 configuration file.
    
    Args:
        root_dir: Project root directory
    """
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
    data,
    results
per-file-ignores =
    __init__.py:F401
"""
    config_path = root_dir / ".flake8"
    if not config_path.exists():
        with open(config_path, 'w') as f:
            f.write(config_content)
        logger.info(f"Created .flake8 config at {config_path}")
    else:
        logger.info(f".flake8 config already exists at {config_path}")

def create_black_config(root_dir: Path) -> None:
    """
    Create a pyproject.toml configuration for Black if it doesn't exist or update it.
    
    Args:
        root_dir: Project root directory
    """
    toml_path = root_dir / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310']
include = '\\.pyi?$'
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
    | data
    | results
)/
'''
"""
    
    if toml_path.exists():
        with open(toml_path, 'r') as f:
            content = f.read()
        
        if '[tool.black]' in content:
            logger.info("Black configuration already exists in pyproject.toml")
            return
        
        with open(toml_path, 'a') as f:
            f.write(black_section)
        logger.info(f"Appended Black config to {toml_path}")
    else:
        with open(toml_path, 'w') as f:
            f.write("[project]\nname = \"llmXive-project\"\nversion = \"0.1.0\"\n")
            f.write(black_section)
        logger.info(f"Created pyproject.toml with Black config at {toml_path}")

def init_pre_commit(root_dir: Path) -> None:
    """
    Initialize pre-commit hooks.
    
    Args:
        root_dir: Project root directory
    """
    pre_commit_path = root_dir / ".pre-commit-config.yaml"
    
    config_content = """repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
- id: black
  language_version: python3
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
- id: flake8
"""
    
    if not pre_commit_path.exists():
        with open(pre_commit_path, 'w') as f:
            f.write(config_content)
        logger.info(f"Created .pre-commit-config.yaml at {pre_commit_path}")
    else:
        logger.info(f".pre-commit-config.yaml already exists at {pre_commit_path}")
    
    # Initialize git hooks if .git exists
    git_dir = root_dir / ".git"
    if git_dir.exists():
        logger.info("Initializing pre-commit hooks...")
        try:
            subprocess.run(
                ["pre-commit", "install"],
                cwd=root_dir,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Pre-commit hooks installed successfully.")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to install pre-commit hooks: {e}")
            logger.info("You can install them manually by running: pre-commit install")
    else:
        logger.info(".git directory not found. Skipping pre-commit hook installation.")

def main() -> None:
    """Main entry point for setting up linting and formatting tools."""
    root_dir = Path(__file__).parent.parent
    logger.info(f"Setting up linting tools in {root_dir}")
    
    # Install dependencies
    install_dev_dependencies()
    
    # Create configuration files
    create_flake8_config(root_dir)
    create_black_config(root_dir)
    init_pre_commit(root_dir)
    
    # Verify installations
    logger.info("Verifying tool installations...")
    flake8_ok = check_tool("flake8")
    black_ok = check_tool("black")
    
    if flake8_ok and black_ok:
        logger.info("Linting setup completed successfully.")
        
        # Run a quick check on the src directory if it exists
        src_dir = root_dir / "code" / "src"
        if src_dir.exists():
            logger.info("Running black --check on code/src/...")
            try:
                subprocess.run(
                    ["black", "--check", str(src_dir)],
                    cwd=root_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info("black --check passed on code/src/")
            except subprocess.CalledProcessError:
                # It's okay if there are formatting issues initially
                logger.info("black --check found formatting issues (expected on first run). Run 'black code/src/' to fix.")
            except FileNotFoundError:
                logger.warning("black command not found during check.")
    else:
        logger.error("Linting setup incomplete. Some tools are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()