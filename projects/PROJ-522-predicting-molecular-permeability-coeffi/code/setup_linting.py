import subprocess
import sys
import os

def run_command(command):
    """Run a shell command and raise on failure."""
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(f"SUCCESS: {command}")
        if result.stdout:
            print(result.stdout)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"FAILED: {command}")
        print(f"Error: {e.stderr}")
        raise

def main():
    """
    Main entry point to install and configure linting tools.
    Installs ruff and ensures black is available.
    """
    print("Installing linting tools...")
    
    # Install ruff
    run_command(f"{sys.executable} -m pip install --upgrade ruff black isort")
    
    print("Linting tools installed successfully.")
    print("Configuration files (ruff.toml, pyproject.toml) are in the code/ directory.")
    print("Run 'ruff check code/' to lint and 'black code/' to format.")

if __name__ == "__main__":
    main()