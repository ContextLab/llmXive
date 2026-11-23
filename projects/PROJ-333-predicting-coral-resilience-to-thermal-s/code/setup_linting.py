"""
Setup script for linting and formatting tools.
Installs and verifies ruff, black, and isort.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, check=True):
    """
    Runs a shell command and returns the result.
    """
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}", file=sys.stderr)
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        if check:
            sys.exit(1)
        return False

def install_tools():
    """
    Installs the required linting and formatting tools.
    """
    tools = [
        "ruff",
        "black",
        "isort",
        "tomli",
        "tomli-w",
        "tomlkit"
    ]
    
    print("Installing linting and formatting tools...")
    for tool in tools:
        print(f"Installing {tool}...")
        if not run_command([sys.executable, "-m", "pip", "install", tool]):
            print(f"Failed to install {tool}", file=sys.stderr)
            return False
    
    print("All tools installed successfully.")
    return True

def verify_tools():
    """
    Verifies that all required tools are installed and accessible.
    """
    tools = ["ruff", "black", "isort"]
    print("\nVerifying tool installation...")
    
    for tool in tools:
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"  {tool}: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            print(f"  {tool}: NOT FOUND", file=sys.stderr)
            return False
        except FileNotFoundError:
            print(f"  {tool}: NOT FOUND (command not found)", file=sys.stderr)
            return False
    
    print("All tools verified.")
    return True

def generate_configs():
    """
    Generates the configuration files for the tools.
    """
    print("\nGenerating configuration files...")
    try:
        from lint_config import main as generate_main
        generate_main()
        return True
    except ImportError as e:
        print(f"Error importing lint_config: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point for setting up the linting environment.
    """
    print("Setting up linting environment for llmXive project...")
    
    if not install_tools():
        print("Installation failed. Exiting.", file=sys.stderr)
        sys.exit(1)
    
    if not verify_tools():
        print("Verification failed. Exiting.", file=sys.stderr)
        sys.exit(1)
    
    if not generate_configs():
        print("Configuration generation failed. Exiting.", file=sys.stderr)
        sys.exit(1)
    
    print("\nLinting environment setup complete.")
    print("Next steps:")
    print("  1. Run 'ruff check .' to lint the codebase")
    print("  2. Run 'black .' to format the codebase")
    print("  3. Run 'ruff check --select I .' to check import sorting")

if __name__ == "__main__":
    main()
