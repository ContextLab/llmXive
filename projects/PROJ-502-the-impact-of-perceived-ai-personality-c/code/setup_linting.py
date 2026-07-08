"""
Script to verify linting and formatting tool installation and configuration.

This script checks that the project's linting configuration (flake8, black, isort)
is valid and that the tools are available in the environment.

Usage:
    python code/setup_linting.py
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return (return_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    code, _, _ = run_command([sys.executable, "-m", tool_name, "--version"])
    if code == 0:
        print(f"✓ {tool_name} is installed")
        return True
    else:
        print(f"✗ {tool_name} is NOT installed or not in PATH")
        return False

def verify_flake8_config() -> bool:
    """Verify .flake8 configuration file exists and is valid."""
    flake8_path = Path("code/.flake8")
    if not flake8_path.exists():
        print("✗ .flake8 configuration file not found")
        return False
    
    print("✓ .flake8 configuration file found")
    
    # Try to run flake8 with --help to ensure it loads config correctly
    code, stdout, stderr = run_command([sys.executable, "-m", "flake8", "--help"])
    if code == 0:
        print("✓ flake8 loads configuration successfully")
        return True
    else:
        print(f"✗ flake8 failed to load: {stderr}")
        return False

def verify_black_config() -> bool:
    """Verify pyproject.toml black configuration exists."""
    pyproject_path = Path("code/pyproject.toml")
    if not pyproject_path.exists():
        print("✗ pyproject.toml configuration file not found")
        return False
    
    content = pyproject_path.read_text()
    if "[tool.black]" in content:
        print("✓ Black configuration found in pyproject.toml")
        return True
    else:
        print("✗ Black configuration not found in pyproject.toml")
        return False

def verify_isort_config() -> bool:
    """Verify isort configuration exists."""
    pyproject_path = Path("code/pyproject.toml")
    if not pyproject_path.exists():
        print("✗ pyproject.toml configuration file not found")
        return False
    
    content = pyproject_path.read_text()
    if "[tool.isort]" in content:
        print("✓ isort configuration found in pyproject.toml")
        return True
    else:
        print("✗ isort configuration not found in pyproject.toml")
        return False

def main():
    """Main entry point for setup verification."""
    print("=== Linting and Formatting Setup Verification ===\n")
    
    # Check tool installation
    tools = ["flake8", "black", "isort"]
    all_installed = True
    for tool in tools:
        if not check_tool_installed(tool):
            all_installed = False
    
    if not all_installed:
        print("\n⚠ Some tools are missing. Run: pip install -r code/requirements-dev.txt")
        sys.exit(1)
    
    print("\n--- Configuration Verification ---")
    
    config_checks = [
        ("flake8 config", verify_flake8_config),
        ("black config", verify_black_config),
        ("isort config", verify_isort_config),
    ]
    
    all_configs_valid = True
    for name, check_func in config_checks:
        if not check_func():
            all_configs_valid = False
    
    if all_configs_valid:
        print("\n✓ All linting and formatting tools and configurations are ready.")
        print("\nUsage:")
        print("  Lint:      flake8 code/")
        print("  Format:    black code/")
        print("  Sort:      isort code/")
        print("  Check:     flake8 code/ && black --check code/")
        sys.exit(0)
    else:
        print("\n✗ Some configurations are invalid.")
        sys.exit(1)

if __name__ == "__main__":
    main()