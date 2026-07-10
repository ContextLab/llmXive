import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False

def main():
    """
    Setup linting (ruff), formatting (black), and pre-commit hooks.
    This script ensures the configuration files exist and installs the hooks.
    """
    root_dir = Path(__file__).parent.resolve()
    print(f"Setting up linting and formatting in: {root_dir}")

    # 1. Ensure dependencies are present (assuming requirements.txt is installed)
    # In a real CI/CD context, this might be handled by the environment setup.
    # Here we just verify the tools are available or install them if not.
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(root_dir / "requirements.txt")], check=True)
    except subprocess.CalledProcessError:
        print("Warning: Could not install requirements. Assuming environment is pre-configured.")

    # 2. Initialize pre-commit if not already done
    # We check if .git/hooks/pre-commit exists or if pre-commit is installed globally
    # For this script, we assume we are setting up the config file which is the primary artifact.
    # The actual hook installation usually happens via `pre-commit install`.
    
    # Verify config files exist (they are created by this task's artifact generation)
    ruff_config = root_dir / ".ruff.toml"
    precommit_config = root_dir / ".pre-commit-config.yaml"
    
    if not ruff_config.exists():
        print(f"Error: {ruff_config} not found. Please ensure the file was created.")
        return False
    
    if not precommit_config.exists():
        print(f"Error: {precommit_config} not found. Please ensure the file was created.")
        return False

    print("Configuration files validated.")
    
    # 3. Attempt to install hooks (optional but recommended for local dev)
    # This might fail if git is not initialized, which is fine for the script logic.
    if os.path.exists(root_dir / ".git"):
        print("Installing pre-commit hooks...")
        if not run_command([sys.executable, "-m", "pre_commit", "install"], cwd=root_dir):
            print("Failed to install pre-commit hooks. Run 'pre-commit install' manually.")
    else:
        print("Git repository not found in current directory. Skipping hook installation.")
        print("To enable hooks, run: pre-commit install")

    print("Linting and formatting setup complete.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)