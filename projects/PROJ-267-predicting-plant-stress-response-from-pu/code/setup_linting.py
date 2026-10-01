import os
import sys
import subprocess
from pathlib import Path
import toml
import logging

# Ensure we can import from the project root if needed, though this script is standalone
# We assume it runs from the project root or code/ directory.

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def check_file_exists(path: Path) -> bool:
    if not path.exists():
        logging.warning(f"Configuration file not found: {path}")
        return False
    return True

def validate_pyproject_config() -> bool:
    pyproject_path = Path("pyproject.toml")
    if not check_file_exists(pyproject_path):
        return False
    
    try:
        with open(pyproject_path, "r") as f:
            config = toml.load(f)
        
        if "tool" not in config:
            logging.error("pyproject.toml missing [tool] section")
            return False
        
        tool_config = config["tool"]
        if "black" not in tool_config:
            logging.error("pyproject.toml missing [tool.black] configuration")
            return False
        
        if "isort" not in tool_config:
            logging.error("pyproject.toml missing [tool.isort] configuration")
            return False
        
        logging.info("pyproject.toml configuration valid.")
        return True
    except Exception as e:
        logging.error(f"Error parsing pyproject.toml: {e}")
        return False

def validate_flake8_config() -> bool:
    flake8_path = Path(".flake8")
    if not check_file_exists(flake8_path):
        logging.error(".flake8 file missing")
        return False
    
    try:
        with open(flake8_path, "r") as f:
            content = f.read()
        
        if "[flake8]" not in content:
            logging.error(".flake8 missing [flake8] section")
            return False
        
        if "max-line-length" not in content:
            logging.warning(".flake8 missing max-line-length setting")
        
        logging.info(".flake8 configuration valid.")
        return True
    except Exception as e:
        logging.error(f"Error parsing .flake8: {e}")
        return False

def validate_precommit_config() -> bool:
    precommit_path = Path(".pre-commit-config.yaml")
    if not check_file_exists(precommit_path):
        logging.error(".pre-commit-config.yaml file missing")
        return False
    
    try:
        with open(precommit_path, "r") as f:
            content = f.read()
        
        required_hooks = ["black", "flake8"]
        missing_hooks = []
        
        for hook in required_hooks:
            if hook not in content:
                missing_hooks.append(hook)
        
        if missing_hooks:
            logging.error(f".pre-commit-config.yaml missing hooks: {missing_hooks}")
            return False
        
        logging.info(".pre-commit-config.yaml configuration valid.")
        return True
    except Exception as e:
        logging.error(f"Error parsing .pre-commit-config.yaml: {e}")
        return False

def install_requirements():
    logging.info("Installing linting and formatting dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "black", "flake8", "isort", "pre-commit", "toml"])
        logging.info("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install dependencies: {e}")
        sys.exit(1)

def run_linting():
    logging.info("Running flake8 linting...")
    try:
        # Run on the code directory
        result = subprocess.run(
            ["flake8", "code/"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("No linting errors found.")
        else:
            logging.warning("Linting errors found:")
            print(result.stdout)
            print(result.stderr)
            # Do not exit with error here, just report
    except FileNotFoundError:
        logging.error("flake8 not found. Please install it.")
    except Exception as e:
        logging.error(f"Error running flake8: {e}")

def run_formatting():
    logging.info("Running black formatting...")
    try:
        result = subprocess.run(
            ["black", "--check", "code/"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Code is already formatted correctly.")
        else:
            logging.warning("Code needs formatting. Run 'black code/' to fix.")
            print(result.stdout)
            print(result.stderr)
    except FileNotFoundError:
        logging.error("black not found. Please install it.")
    except Exception as e:
        logging.error(f"Error running black: {e}")

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting linting and formatting setup validation...")
    
    # Install dependencies if missing
    install_requirements()
    
    # Validate configuration files
    pyproject_ok = validate_pyproject_config()
    flake8_ok = validate_flake8_config()
    precommit_ok = validate_precommit_config()
    
    if not (pyproject_ok and flake8_ok and precommit_ok):
        logger.error("Configuration validation failed. Please fix the issues above.")
        sys.exit(1)
    
    # Run checks
    run_linting()
    run_formatting()
    
    logger.info("Linting and formatting setup validation complete.")

if __name__ == "__main__":
    main()
