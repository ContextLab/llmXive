"""
Setup script for linting and formatting tools.
Verifies installation and runs initial checks on the codebase.
"""
import subprocess
import sys
import os

def run_command(cmd: list[str], description: str) -> bool:
    """Execute a command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        return False

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    # Check if tools are installed
    tools = [
        ("ruff", "ruff --version"),
        ("black", "black --version"),
    ]

    for tool, cmd_str in tools:
        print(f"Checking {tool}...")
        try:
            subprocess.run(cmd_str.split(), check=True, capture_output=True)
            print(f"  ✓ {tool} found")
        except subprocess.CalledProcessError:
            print(f"  ✗ {tool} not found. Installing...")
            if not run_command([sys.executable, "-m", "pip", "install", tool], f"Install {tool}"):
                print(f"Failed to install {tool}. Exiting.")
                return 1

    print("\n--- Running Linter (Ruff) ---")
    # Run linter on the code directory (excluding itself if necessary, but usually fine)
    if not run_command(["ruff", "check", "."], "Ruff check"):
        print("Linter found issues. Run 'ruff check --fix' to auto-fix where possible.")
    else:
        print("Linter passed.")

    print("\n--- Running Formatter (Black) ---")
    # Run formatter in check mode first
    if not run_command(["black", "--check", "."], "Black check"):
        print("Formatter found issues. Run 'black .' to auto-format.")
    else:
        print("Formatter passed.")

    print("\nLinting and formatting tools configured successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
