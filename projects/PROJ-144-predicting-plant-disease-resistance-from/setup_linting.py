import subprocess
import sys
from pathlib import Path
from utils.constants import PROJECT_ROOT

def install_dependencies():
    """Install pre-commit and related tools."""
    print("Installing pre-commit...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pre-commit"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "black", "flake8", "isort"])

def setup_pre_commit():
    """Initialize pre-commit hooks."""
    print("Initializing pre-commit hooks...")
    try:
        subprocess.check_call(["pre-commit", "install"], cwd=PROJECT_ROOT)
        print("Pre-commit hooks installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install pre-commit hooks: {e}")
        raise

def create_linting_config_files():
    """Create configuration files for linting tools."""
    # .flake8 is created as a separate artifact in this task
    # isort configuration is handled via black profile in .pre-commit-config.yaml
    pass

def run_initial_lint_check():
    """Run an initial lint check to verify configuration."""
    print("Running initial lint check...")
    try:
        subprocess.check_call(["pre-commit", "run", "--all-files"], cwd=PROJECT_ROOT)
        print("Initial lint check passed.")
    except subprocess.CalledProcessError as e:
        print(f"Initial lint check failed. Please fix the issues.")
        # Do not raise here to allow the script to complete and report status

def main():
    """Main entry point for setup_linting."""
    install_dependencies()
    create_linting_config_files()
    setup_pre_commit()
    run_initial_lint_check()
    print("Linting setup complete.")

if __name__ == "__main__":
    main()