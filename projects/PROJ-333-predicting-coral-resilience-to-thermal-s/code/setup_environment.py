import subprocess
import sys
import os

def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Runs a shell command."""
    return subprocess.run(cmd, check=check)

def check_python_version(min_version: tuple = (3, 9)) -> bool:
    """Checks if the current Python version meets the minimum requirement."""
    current = (sys.version_info.major, sys.version_info.minor)
    return current >= min_version

def install_dependencies(requirements_file: str = "requirements.txt") -> None:
    """Installs dependencies from requirements.txt."""
    run_command([sys.executable, "-m", "pip", "install", "-r", requirements_file])

def verify_plink2() -> bool:
    """Verifies if Plink2 is installed and accessible."""
    try:
        run_command(["plink2", "--version"], check=False)
        return True
    except FileNotFoundError:
        return False

def main():
    """Main entry point for environment setup."""
    if not check_python_version():
        print("Python 3.9+ is required.")
        sys.exit(1)
    install_dependencies()
    if not verify_plink2():
        print("Warning: Plink2 not found. Install it manually.")

if __name__ == "__main__":
    main()
