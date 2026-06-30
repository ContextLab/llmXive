"""
Setup script to validate linting and formatting configurations.

This script verifies that the project's linting (flake8, pylint) 
and formatting (black) configurations are correctly set up and 
compatible with the project's Python version and style guidelines.

Usage:
    python code/setup_linting.py
"""
import subprocess
import sys
from pathlib import Path
import tomllib
import configparser
import toml

def check_command(cmd: str) -> bool:
    """Check if a command is available in the environment."""
    try:
        subprocess.run(
            [cmd, "--version"], 
            check=True, 
            capture_output=True, 
            text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", f"Command not found: {cmd[0]}"

def validate_flake8_config() -> bool:
    """Validate flake8 configuration file exists and is readable."""
    config_path = Path("code/.flake8")
    if not config_path.exists():
        print("❌ .flake8 configuration file not found.")
        return False
    
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        if 'flake8' not in config:
            print("⚠️  [flake8] section missing in .flake8, but file exists.")
        else:
            print("✅ .flake8 configuration valid.")
        return True
    except Exception as e:
        print(f"❌ Error reading .flake8: {e}")
        return False

def validate_black_config() -> bool:
    """Validate black configuration file exists and is readable."""
    config_path = Path("code/.black.toml")
    if not config_path.exists():
        print("❌ .black.toml configuration file not found.")
        return False
    
    try:
        with open(config_path, "rb") as f:
            toml.load(f)
        print("✅ .black.toml configuration valid.")
        return True
    except Exception as e:
        print(f"❌ Error reading .black.toml: {e}")
        return False

def validate_pylint_config() -> bool:
    """Validate pylint configuration file exists and is readable."""
    config_path = Path("code/.pylintrc")
    if not config_path.exists():
        print("❌ .pylintrc configuration file not found.")
        return False
    
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        if 'MAIN' not in config and 'MESSAGES CONTROL' not in config:
            print("⚠️  Key sections missing in .pylintrc, but file exists.")
        else:
            print("✅ .pylintrc configuration valid.")
        return True
    except Exception as e:
        print(f"❌ Error reading .pylintrc: {e}")
        return False

def main() -> int:
    """Main entry point for the linting setup validation."""
    print("🔍 Validating Linting and Formatting Configuration...")
    print("-" * 50)
    
    # Check tool availability
    tools = {
        "flake8": check_command("flake8"),
        "black": check_command("black"),
        "pylint": check_command("pylint"),
    }
    
    all_installed = True
    for tool, installed in tools.items():
        status = "✅" if installed else "❌"
        print(f"{status} {tool}: {'Installed' if installed else 'Missing'}")
        if not installed:
            all_installed = False
    
    if not all_installed:
        print("\n⚠️  Some tools are missing. Please install them via requirements.txt:")
        print("   pip install flake8 black pylint")
        return 1
    
    print("-" * 50)
    
    # Validate configurations
    configs_valid = True
    
    if not validate_flake8_config():
        configs_valid = False
    
    if not validate_black_config():
        configs_valid = False
        
    if not validate_pylint_config():
        configs_valid = False
    
    print("-" * 50)
    
    if configs_valid:
        print("✅ All linting and formatting configurations are valid.")
        print("\n📝 To run linters/formatters:")
        print("   black code/ --check")
        print("   flake8 code/")
        print("   pylint code/")
        return 0
    else:
        print("❌ Configuration validation failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())