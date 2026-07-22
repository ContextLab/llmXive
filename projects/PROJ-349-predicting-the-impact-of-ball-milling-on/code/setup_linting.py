import subprocess
import sys
from pathlib import Path
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_tool(tool_name: str) -> bool:
    """Check if a linting/formatting tool is installed."""
    try:
        result = subprocess.run(
            [tool_name, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"{tool_name} version: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        logger.error(f"{tool_name} is not installed or not in PATH.")
        return False
    except FileNotFoundError:
        logger.error(f"{tool_name} command not found.")
        return False

def install_dev_dependencies() -> bool:
    """Install flake8 and black using pip."""
    packages = ["flake8", "black"]
    try:
        logger.info("Installing development dependencies: flake8, black")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def create_flake8_config(project_root: Path) -> None:
    """Create a .flake8 configuration file."""
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
"""
    config_path = project_root / ".flake8"
    with open(config_path, "w") as f:
        f.write(config_content)
    logger.info(f"Created .flake8 configuration at {config_path}")

def create_black_config(project_root: Path) -> None:
    """Create a pyproject.toml with black configuration if not exists."""
    config_path = project_root / "pyproject.toml"
    black_section = """[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
"""
    
    if config_path.exists():
        with open(config_path, "r") as f:
            content = f.read()
        if "[tool.black]" not in content:
            with open(config_path, "a") as f:
                f.write("\n" + black_section)
            logger.info(f"Appended black config to {config_path}")
        else:
            logger.info(f"Black config already exists in {config_path}")
    else:
        with open(config_path, "w") as f:
            f.write(black_section)
        logger.info(f"Created pyproject.toml with black config at {config_path}")

def init_pre_commit(project_root: Path) -> None:
    """Initialize pre-commit configuration."""
    config_content = """repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
- id: black
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
- id: flake8
"""
    config_path = project_root / ".pre-commit-config.yaml"
    with open(config_path, "w") as f:
        f.write(config_content)
    logger.info(f"Created .pre-commit-config.yaml at {config_path}")

def main() -> int:
    """Main entry point for setup linting."""
    project_root = Path(__file__).resolve().parent.parent
    
    # Install dependencies if needed
    if not (check_tool("flake8") and check_tool("black")):
        logger.info("Attempting to install missing dependencies...")
        if not install_dev_dependencies():
            logger.error("Failed to install dependencies. Exiting.")
            return 1
    
    # Verify tools again after installation
    if not (check_tool("flake8") and check_tool("black")):
        logger.error("Tools still not available after installation.")
        return 1

    # Create configuration files
    create_flake8_config(project_root)
    create_black_config(project_root)
    init_pre_commit(project_root)

    # Run black check on src/ if it exists
    src_dir = project_root / "src"
    if src_dir.exists():
        logger.info(f"Running 'black --check {src_dir}'...")
        try:
            subprocess.run(
                ["black", "--check", str(src_dir)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("black --check passed on src/")
        except subprocess.CalledProcessError as e:
            logger.warning(f"black --check found formatting issues in src/:\n{e.stdout}\n{e.stderr}")
            # Note: We do not fail here, as the task is to configure linting.
            # The check is informational.

    logger.info("Linting configuration complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())