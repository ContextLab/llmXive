import subprocess
import sys
import os

def run_command(cmd: list[str]) -> bool:
    """Run a shell command and return True if successful."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.returncode == 0:
            return True
        return False
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        return False
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        print("Ensure black and flake8 are installed.")
        return False

def main():
    """Execute verification commands for linting and formatting."""
    print("Running linting and formatting verification...")
    
    # Check if black is installed
    if not run_command([sys.executable, "-m", "pip", "install", "-q", "black", "flake8"]):
        print("Failed to install dependencies.")
        return 1

    # Run black check
    print("\n--- Running black --check . ---")
    black_success = run_command(["black", "--check", "."])
    
    # Run flake8 check
    print("\n--- Running flake8 code/ ---")
    flake8_success = run_command(["flake8", "code/"])

    if black_success and flake8_success:
        print("\n✓ All linting and formatting checks passed.")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
