"""
Script to install and configure linting (ruff) and formatting (black) tools.
This script ensures the necessary tools are installed and configuration files are in place.
"""
import subprocess
import sys
from pathlib import Path

def run_command(command: list[str], description: str) -> bool:
    """Run a shell command and report success/failure."""
    print(f"Running: {description}")
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✓ {description} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        return False

def main():
    """Main entry point for setting up linting and formatting."""
    print("Setting up linting (ruff) and formatting (black) tools...")

    # Install tools
    success = True
    success &= run_command(
        [sys.executable, "-m", "pip", "install", "ruff", "black"],
        "Installing ruff and black"
    )

    if not success:
        print("Failed to install tools. Please install manually: pip install ruff black")
        sys.exit(1)

    # Verify installation
    run_command(
        [sys.executable, "-m", "ruff", "--version"],
        "Verifying ruff installation"
    )
    run_command(
        [sys.executable, "-m", "black", "--version"],
        "Verifying black installation"
    )

    # Check existing configuration
    root = Path(__file__).parent.parent
    ruff_config = root / ".ruff.toml"
    pyproject = root / "pyproject.toml"

    if ruff_config.exists():
        print(f"Found existing ruff config at {ruff_config}")
    else:
        print(f"No ruff config found at {ruff_config}. Creating default...")
        # Create a minimal ruff config if missing
        ruff_config.write_text(
            "[lint]\nselect = [\"E\", \"W\", \"F\", \"I\", \"B\", \"C4\"]\nignore = [\"E501\"]\n"
        )

    if pyproject.exists():
        print(f"Found existing pyproject.toml at {pyproject}")
    else:
        print(f"No pyproject.toml found at {pyproject}. Creating default...")
        pyproject.write_text(
            "[tool.black]\nline-length = 88\ntarget-version = ['py310']\n"
        )

    print("Setup complete. You can now run:")
    print("  ruff check .        # Check for linting issues")
    print("  ruff format .       # Format code with ruff (or use black)")
    print("  black .             # Format code with black")

if __name__ == "__main__":
    main()
