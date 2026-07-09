import subprocess
import sys
from pathlib import Path

def run_black():
    """Run black formatter on the code directory."""
    result = subprocess.run([sys.executable, "-m", "black", "code/"], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    return result.returncode

def run_flake8():
    """Run flake8 linter on the code directory."""
    result = subprocess.run([sys.executable, "-m", "flake8", "code/"], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    return result.returncode

def run_pylint():
    """Run pylint linter on the code directory."""
    result = subprocess.run([sys.executable, "-m", "pylint", "code/"], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
    return result.returncode

def main():
    """Run all linting and formatting tools."""
    print("Running Black...")
    run_black()
    print("\nRunning Flake8...")
    run_flake8()
    print("\nRunning Pylint...")
    run_pylint()

if __name__ == "__main__":
    main()
