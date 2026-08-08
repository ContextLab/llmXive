"""
Script to verify and install linting/formatter tools (black, flake8, isort).
This script ensures the development environment is ready for code quality checks.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        if check:
            raise
        return e

def main():
    """Main entry point to setup linting tools."""
    project_root = Path(__file__).parent.parent
    config_files = {
        "pyproject.toml": "Black and Isort configuration",
        ".flake8": "Flake8 configuration",
        ".isort.cfg": "Isort configuration",
    }

    print(f"Checking linting configuration in {project_root}...")

    # Verify config files exist
    missing_configs = []
    for filename, desc in config_files.items():
        path = project_root / filename
        if not path.exists():
            missing_configs.append(f"{filename} ({desc})")
        else:
            print(f"  ✓ Found {filename}")

    if missing_configs:
        print(f"Error: Missing configuration files: {', '.join(missing_configs)}")
        sys.exit(1)

    # Check if tools are installed
    tools = ["black", "flake8", "isort"]
    missing_tools = []

    for tool in tools:
        try:
            run_command([sys.executable, "-m", tool, "--version"], check=False)
            print(f"  ✓ {tool} is installed")
        except Exception:
            missing_tools.append(tool)

    if missing_tools:
        print(f"Installing missing tools: {', '.join(missing_tools)}")
        run_command([sys.executable, "-m", "pip", "install"] + [f"{t}>=6.0.0" if t != "black" else "black>=23.0.0" for t in missing_tools])
        print("Tools installed successfully.")
    else:
        print("All linting tools are already installed.")

    # Run a dry-run check on the code directory to verify configs work
    code_dir = project_root / "code"
    if code_dir.exists():
        print("\nRunning dry-run validation on code directory...")
        # Check flake8
        run_command([sys.executable, "-m", "flake8", str(code_dir), "--count", "--select=E9,F63,F7,F82", "--show-source", "--statistics"], check=False)
        # Check isort (check only)
        run_command([sys.executable, "-m", "isort", str(code_dir), "--check-only"], check=False)
        # Check black (diff only)
        run_command([sys.executable, "-m", "black", str(code_dir), "--diff", "--check"], check=False)

    print("\nLinting setup verification complete.")

if __name__ == "__main__":
    main()