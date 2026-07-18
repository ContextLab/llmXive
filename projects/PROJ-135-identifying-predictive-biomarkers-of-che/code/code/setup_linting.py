import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """Execute a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
            shell=False,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        if check:
            sys.exit(1)
        return e


def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed in the current environment."""
    try:
        subprocess.run(
            [tool_name, "--version"],
            check=True,
            capture_output=True,
            text=True,
            shell=False,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_tools():
    """Install ruff and black if not present."""
    print("Checking and installing linting tools...")
    tools = [("ruff", "ruff"), ("black", "black")]
    for name, pkg in tools:
        if not check_tool_installed(name):
            print(f"Installing {name}...")
            run_command([sys.executable, "-m", "pip", "install", pkg])
        else:
            print(f"{name} is already installed.")


def verify_config_files():
    """Verify that configuration files exist in the project root."""
    root = Path(__file__).resolve().parent
    config_files = [
        root / ".ruff.toml",
        root / "pyproject.toml",
    ]
    missing = [f for f in config_files if not f.exists()]
    if missing:
        print(f"Warning: Missing configuration files: {missing}")
        print("Please ensure .ruff.toml and pyproject.toml are present.")
        return False
    print("Configuration files verified.")
    return True


def run_ruff_check():
    """Run ruff check on the codebase."""
    root = Path(__file__).resolve().parent
    print("Running ruff check...")
    run_command(["ruff", "check", str(root)], check=False)


def run_ruff_format():
    """Run ruff format on the codebase."""
    root = Path(__file__).resolve().parent
    print("Running ruff format...")
    run_command(["ruff", "format", str(root)], check=False)


def run_black_check():
    """Run black --check on the codebase."""
    root = Path(__file__).resolve().parent
    print("Running black --check...")
    run_command(["black", "--check", str(root)], check=False)


def main():
    """Main entry point for the setup_linting script."""
    print("=== Linting and Formatting Setup ===")
    install_tools()
    if not verify_config_files():
        print("Configuration verification failed. Please check manually.")
    else:
        print("\n--- Running Checks ---")
        run_ruff_check()
        run_black_check()
        print("\n--- Running Formatters ---")
        run_ruff_format()
        # Note: ruff format usually supersedes black, but we run both if configured
        print("Linting setup complete.")


if __name__ == "__main__":
    main()