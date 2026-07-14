"""
Setup script for linting (ruff) and formatting (black) tools.
Installs tools via pip and ensures configuration files exist.
"""
import subprocess
import sys
from pathlib import Path
import json

def install_tools():
    """Install ruff and black if not present."""
    print("Checking and installing linting tools...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
        print("Successfully installed ruff and black.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing tools: {e}")
        sys.exit(1)

def ensure_config_file():
    """Ensure pyproject.toml exists with basic configuration."""
    project_root = Path(__file__).parent.parent
    config_path = project_root / "pyproject.toml"

    if not config_path.exists():
        print("Creating pyproject.toml configuration...")
        # Minimal config content as fallback if not manually created
        config_content = {
            "tool": {
                "black": {
                    "line-length": 88,
                    "target-version": ["py311"],
                },
                "ruff": {
                    "line-length": 88,
                    "target-version": "py311",
                    "select": ["E", "W", "F", "I", "B", "C4"],
                    "ignore": ["E501"],
                }
            }
        }
        with open(config_path, "w") as f:
            # Writing a simple TOML structure manually to avoid dependency on toml lib
            f.write('[build-system]\n')
            f.write('requires = ["setuptools>=61.0", "wheel"]\n')
            f.write('build-backend = "setuptools.build_meta"\n\n')
            f.write('[project]\n')
            f.write('name = "llmxive-brain-music"\n')
            f.write('version = "0.1.0"\n\n')
            f.write('[tool.black]\n')
            f.write('line-length = 88\n')
            f.write('target-version = ["py311"]\n\n')
            f.write('[tool.ruff]\n')
            f.write('line-length = 88\n')
            f.write('target-version = "py311"\n')
            f.write('select = ["E", "W", "F", "I", "B", "C4"]\n')
            f.write('ignore = ["E501"]\n')
        print(f"Created {config_path}")
    else:
        print(f"Configuration file {config_path} already exists.")

def main():
    """Main entry point for setup script."""
    print("=== Linting and Formatting Setup ===")
    install_tools()
    ensure_config_file()
    print("Setup complete. You can now run `ruff check .` and `black .`")

if __name__ == "__main__":
    main()