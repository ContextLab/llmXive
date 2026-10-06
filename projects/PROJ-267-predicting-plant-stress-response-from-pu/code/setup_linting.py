import os
import sys
import subprocess
from pathlib import Path
import logging
import toml

# Ensure we can import sibling modules if needed, though this script is standalone
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = PROJECT_ROOT / "code"

def setup_logging():
    """Configure basic logging for the setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_file_exists(path: Path) -> bool:
    """Check if a file exists at the given path."""
    return path.exists()

def validate_pyproject_config(config_path: Path) -> bool:
    """Validate that pyproject.toml exists and contains black/flake8 config."""
    if not check_file_exists(config_path):
        logging.warning(f"{config_path} not found. Creating a minimal configuration.")
        return False

    try:
        with open(config_path, 'r') as f:
            content = f.read()
            # Basic check for presence of tool sections
            has_black = '[tool.black]' in content
            has_flake8 = '[tool.flake8]' in content or '[tool:flake8]' in content
            if not has_black:
                logging.warning("Missing [tool.black] section in pyproject.toml")
            if not has_flake8:
                logging.warning("Missing [tool.flake8] section in pyproject.toml")
            return has_black and has_flake8
    except Exception as e:
        logging.error(f"Error reading {config_path}: {e}")
        return False

def validate_flake8_config(config_path: Path) -> bool:
    """Validate flake8 configuration."""
    # flake8 can read from setup.cfg, tox.ini, or .flake8, but we prioritize pyproject.toml
    # If pyproject.toml is valid, we assume flake8 config is present if checked there
    return True

def validate_precommit_config(config_path: Path) -> bool:
    """Validate .pre-commit-config.yaml exists."""
    # We don't strictly require pre-commit for T003, but it's good practice
    if not check_file_exists(config_path):
        logging.info(f"{config_path} not found. Skipping pre-commit validation.")
        return True
    return True

def install_requirements():
    """Install flake8 and black if not present."""
    logging.info("Checking/installing linting and formatting tools...")
    packages = ['flake8', 'black']
    for pkg in packages:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'show', pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info(f"{pkg} is already installed.")
        except subprocess.CalledProcessError:
            logging.info(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])

def run_linting():
    """Run flake8 on the code directory."""
    logging.info("Running flake8 linting...")
    try:
        # Run flake8 on the code directory
        result = subprocess.run(
            ['flake8', str(CODE_DIR)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logging.info("Flake8 linting passed.")
        else:
            logging.warning("Flake8 found issues:")
            print(result.stdout)
            print(result.stderr)
    except FileNotFoundError:
        logging.error("flake8 not found. Please ensure it is installed.")
    except Exception as e:
        logging.error(f"Error running flake8: {e}")

def run_formatting():
    """Run black formatting on the code directory."""
    logging.info("Running black formatting...")
    try:
        result = subprocess.run(
            ['black', '--check', str(CODE_DIR)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            logging.info("Black formatting check passed.")
        else:
            logging.warning("Black formatting issues found. Run 'black .' to fix.")
            print(result.stdout)
            print(result.stderr)
    except FileNotFoundError:
        logging.error("black not found. Please ensure it is installed.")
    except Exception as e:
        logging.error(f"Error running black: {e}")

def main():
    """Main entry point for the linting setup task."""
    setup_logging()
    logging.info(f"Starting linting and formatting configuration for project at {PROJECT_ROOT}")

    # Ensure tools are installed
    install_requirements()

    # Create or update pyproject.toml if missing necessary sections
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    if not validate_pyproject_config(pyproject_path):
        logging.info("Updating pyproject.toml with linting configurations...")
        config = {}
        if pyproject_path.exists():
            try:
                with open(pyproject_path, 'r') as f:
                    config = toml.load(f)
            except Exception:
                config = {}

        # Add Black config
        if 'tool' not in config:
            config['tool'] = {}
        config['tool']['black'] = {
            'line-length': 88,
            'target-version': ['py38', 'py39', 'py310', 'py311'],
            'include': r'\.pyi?$'
        }

        # Add Flake8 config
        config['tool']['flake8'] = {
            'max-line-length': 88,
            'extend-ignore': 'E203, W503',
            'exclude': ['venv', '.git', '__pycache__'],
            'per-file-ignores': {}
        }

        with open(pyproject_path, 'w') as f:
            toml.dump(config, f)
        logging.info(f"Updated {pyproject_path}")

    # Run checks
    run_linting()
    run_formatting()

    logging.info("Linting and formatting configuration complete.")

if __name__ == "__main__":
    main()
