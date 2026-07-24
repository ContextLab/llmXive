import subprocess
import sys
from pathlib import Path
import os
import tomli_w
import tomli

def check_tool(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run([tool_name, "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tools() -> None:
    """Install ruff and black if not present."""
    if not check_tool("ruff"):
        print("Installing ruff...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff"])
    if not check_tool("black"):
        print("Installing black...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "black"])

def create_ruff_config(project_root: Path) -> None:
    """Create a ruff.toml configuration file."""
    config_path = project_root / "ruff.toml"
    if config_path.exists():
        print(f"ruff.toml already exists at {config_path}")
        return

    config_content = {
        "target-version": "py311",
        "line-length": 88,
        "select": [
            "E",   # pycodestyle errors
            "W",   # pycodestyle warnings
            "F",   # pyflakes
            "I",   # isort
            "B",   # flake8-bugbear
            "C4",  # flake8-comprehensions
            "UP",  # pyupgrade
        ],
        "ignore": [
            "E501",  # line too long (handled by black)
        ],
        "exclude": [
            ".git",
            "__pycache__",
            "*.egg-info",
            ".mypy_cache",
            ".pytest_cache",
        ],
    }

    with open(config_path, "wb") as f:
        tomli_w.dump(config_content, f)
    print(f"Created ruff.toml at {config_path}")

def create_black_config(project_root: Path) -> None:
    """Create a pyproject.toml with black configuration."""
    config_path = project_root / "pyproject.toml"
    
    # Read existing if present
    existing_config = {}
    if config_path.exists():
        try:
            with open(config_path, "rb") as f:
                existing_config = tomli.load(f)
        except Exception:
            pass

    if "tool" not in existing_config:
        existing_config["tool"] = {}
    if "black" not in existing_config["tool"]:
        existing_config["tool"]["black"] = {}

    black_config = existing_config["tool"]["black"]
    black_config["line-length"] = 88
    black_config["target-version"] = ["py311"]
    black_config["skip-string-normalization"] = False
    black_config["exclude"] = r"/(\.git|__pycache__|\.egg-info|\.mypy_cache|\.pytest_cache)/"

    with open(config_path, "wb") as f:
        tomli_w.dump(existing_config, f)
    print(f"Updated pyproject.toml with black config at {config_path}")

def verify_setup(project_root: Path) -> bool:
    """Verify that linting and formatting tools are configured correctly."""
    ruff_ok = check_tool("ruff")
    black_ok = check_tool("black")
    ruff_config_ok = (project_root / "ruff.toml").exists()
    pyproject_ok = (project_root / "pyproject.toml").exists()

    print(f"Ruff installed: {ruff_ok}")
    print(f"Black installed: {black_ok}")
    print(f"ruff.toml exists: {ruff_config_ok}")
    print(f"pyproject.toml exists: {pyproject_ok}")

    return ruff_ok and black_ok and ruff_config_ok and pyproject_ok

def main() -> int:
    """Main entry point for setting up linting and formatting."""
    project_root = Path(__file__).resolve().parent.parent
    
    print("Setting up linting (ruff) and formatting (black)...")
    
    install_tools()
    create_ruff_config(project_root)
    create_black_config(project_root)
    
    if verify_setup(project_root):
        print("Setup complete. Tools are ready to use.")
        return 0
    else:
        print("Setup failed. Some tools or configurations are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
