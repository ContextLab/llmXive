import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e.cmd}\n{e.stderr}")
        raise

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        run_command([tool_name, "--version"], check=False)
        return True
    except Exception:
        return False

def install_tools() -> None:
    """Install ruff and black if not present."""
    print("Checking/Installing linting tools...")
    if not check_tool_installed("ruff"):
        print("Installing ruff...")
        run_command([sys.executable, "-m", "pip", "install", "ruff"])
    
    if not check_tool_installed("black"):
        print("Installing black...")
        run_command([sys.executable, "-m", "pip", "install", "black"])
    
    print("Tools ready.")

def verify_config_files() -> None:
    """Verify that configuration files exist."""
    config_path = Path(__file__).parent / "pyproject.toml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    print(f"Configuration verified: {config_path}")

def run_ruff_check() -> None:
    """Run ruff check on the project."""
    print("Running ruff check...")
    run_command(["ruff", "check", "code/src", "code/tests"])
    print("Ruff check passed.")

def run_ruff_format() -> None:
    """Run ruff format on the project."""
    print("Running ruff format...")
    run_command(["ruff", "format", "code/src", "code/tests"])
    print("Ruff format applied.")

def run_black_check() -> None:
    """Run black --check on the project."""
    print("Running black --check...")
    run_command(["black", "--check", "code/src", "code/tests"])
    print("Black check passed.")

def main() -> None:
    """Main entry point for setup and verification."""
    print("Setting up linting and formatting tools...")
    install_tools()
    verify_config_files()
    
    print("\n--- Running Checks ---")
    try:
        run_ruff_check()
        run_black_check()
        print("\nAll checks passed!")
    except subprocess.CalledProcessError:
        print("\nSome checks failed. Run 'python setup_linting.py fix' to auto-fix.")
        sys.exit(1)

    print("\n--- Applying Fixes ---")
    try:
        run_ruff_format()
        run_command(["black", "code/src", "code/tests"])
        print("Auto-fixes applied.")
    except subprocess.CalledProcessError as e:
        print(f"Fixes encountered issues: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()