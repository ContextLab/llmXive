"""
Setup script for linting and formatting tools (ruff, black).
Creates configuration files and installs tools if necessary.
"""
import os
import subprocess
import sys
from pathlib import Path
import tomlkit

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run([tool_name, "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool_name: str) -> None:
    """Install a tool using pip."""
    print(f"Installing {tool_name}...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", tool_name], check=True)
        print(f"{tool_name} installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {tool_name}: {e}")
        sys.exit(1)

def verify_config_files() -> None:
    """Verify that configuration files exist or create them."""
    root = Path(__file__).parent.parent
    ruff_config = root / "pyproject.toml"
    black_config = root / "pyproject.toml" # Black uses pyproject.toml too

    if not ruff_config.exists():
        print("pyproject.toml not found. Creating with ruff config...")
        create_ruff_config(root)
    else:
        print("pyproject.toml found. Checking for ruff config...")
        # Simple check, could be more robust
        with open(ruff_config, 'r') as f:
            content = f.read()
            if '[tool.ruff]' not in content:
                print("Ruff config not found in pyproject.toml. Appending...")
                with open(ruff_config, 'a') as f:
                    f.write("\n[tool.ruff]\nline-length = 100\n")
                    f.write("select = [\"E\", \"W\", \"F\", \"I\", \"B\", \"C4\"]\n")
                    f.write("ignore = []\n")

def create_ruff_config(project_root: Path) -> None:
    """Create a pyproject.toml with ruff configuration."""
    config_content = """[tool.ruff]
line-length = 100
select = ["E", "W", "F", "I", "B", "C4"]
ignore = []
target-version = "py39"

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"""
    config_path = project_root / "pyproject.toml"
    with open(config_path, 'w') as f:
        f.write(config_content)
    print(f"Created ruff config at {config_path}")

def create_black_config(project_root: Path) -> None:
    """Ensure black config exists in pyproject.toml."""
    config_path = project_root / "pyproject.toml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            content = f.read()
        if '[tool.black]' not in content:
            with open(config_path, 'a') as f:
                f.write("\n[tool.black]\nline-length = 100\ntarget-version = ['py39']\n")
            print("Added black config to pyproject.toml")
        else:
            print("Black config already exists in pyproject.toml")
    else:
        # If pyproject.toml doesn't exist, create it with both configs
        create_ruff_config(project_root)
        create_black_config(project_root)

def main() -> None:
    """Main entry point for setup_linting."""
    print("Setting up linting and formatting tools...")

    # Install ruff if not present
    if not check_tool_installed("ruff"):
        install_tool("ruff")

    # Verify/create config files
    project_root = Path(__file__).parent.parent
    verify_config_files()
    create_black_config(project_root)

    print("Linting setup complete.")
    print("Run 'ruff check .' to check for linting errors.")
    print("Run 'ruff format .' to format code (if ruff format is available).")

if __name__ == "__main__":
    main()