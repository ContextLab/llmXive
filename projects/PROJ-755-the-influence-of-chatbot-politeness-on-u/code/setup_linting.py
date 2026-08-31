"""
Setup script for linting (ruff/flake8) and formatting (black) tools.
Creates configuration files and installs dependencies if missing.
"""
import os
import sys
import tomllib
import configparser
import argparse
from pathlib import Path
from typing import Optional, Tuple

# Dependency check
try:
    import tomllib
except ImportError:
    # Python < 3.11 needs tomli
    try:
        import tomli as tomllib
    except ImportError:
        print("Error: 'tomli' package required for TOML parsing on Python < 3.11")
        sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
RUFF_CONFIG_PATH = PROJECT_ROOT / "ruff.toml"
FLAKE8_CONFIG_PATH = PROJECT_ROOT / ".flake8"

def check_file_exists(path: Path, name: str) -> bool:
    """Check if a file exists."""
    return path.exists()

def validate_ruff_config() -> Tuple[bool, Optional[str]]:
    """Validate ruff.toml or [tool.ruff] in pyproject.toml."""
    if RUFF_CONFIG_PATH.exists():
        return True, None
    if PYPROJECT_PATH.exists():
        try:
            with open(PYPROJECT_PATH, "rb") as f:
                config = tomllib.load(f)
            if "tool" in config and "ruff" in config["tool"]:
                return True, None
        except Exception:
            pass
    return False, "ruff configuration not found"

def validate_pyproject_black() -> Tuple[bool, Optional[str]]:
    """Validate [tool.black] in pyproject.toml."""
    if not PYPROJECT_PATH.exists():
        return False, "pyproject.toml not found"
    try:
        with open(PYPROJECT_PATH, "rb") as f:
            config = tomllib.load(f)
        if "tool" in config and "black" in config["tool"]:
            return True, None
    except Exception:
        pass
    return False, "black configuration not found in pyproject.toml"

def validate_flake8_config() -> Tuple[bool, Optional[str]]:
    """Validate .flake8 or setup.cfg [flake8]."""
    if FLAKE8_CONFIG_PATH.exists():
        return True, None
    setup_cfg = PROJECT_ROOT / "setup.cfg"
    if setup_cfg.exists():
        config = configparser.ConfigParser()
        try:
            config.read(setup_cfg)
            if "flake8" in config:
                return True, None
        except Exception:
            pass
    return False, "flake8 configuration not found"

def create_ruff_config() -> None:
    """Create a default ruff.toml."""
    content = """# Ruff configuration for llmXive project

line-length = 88
target-version = "py39"

[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["utils", "code"]
"""
    with open(RUFF_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {RUFF_CONFIG_PATH}")

def create_black_config() -> None:
    """Create or update pyproject.toml with black config."""
    black_section = """
[tool.black]
line-length = 88
target-version = ['py39']
include = '\\.pyi?$'
"""
    if not PYPROJECT_PATH.exists():
        # Create new pyproject.toml
        with open(PYPROJECT_PATH, "w", encoding="utf-8") as f:
            f.write("[project]\nname = \"llmXive\"\n")
            f.write(black_section)
    else:
        # Append if not present
        with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        if "[tool.black]" not in content:
            with open(PYPROJECT_PATH, "a", encoding="utf-8") as f:
                f.write(black_section)
    print(f"Updated {PYPROJECT_PATH} with black configuration")

def create_flake8_config() -> None:
    """Create a default .flake8 file."""
    content = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist
extend-ignore = E203, E501
"""
    with open(FLAKE8_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {FLAKE8_CONFIG_PATH}")

def install_linting_tools() -> None:
    """Check if linting tools are installed and install if missing."""
    tools = ["ruff", "black", "flake8"]
    missing = []
    for tool in tools:
        try:
            __import__(tool.replace("-", "_"))
        except ImportError:
            # Try checking via subprocess if import fails but package exists
            import subprocess
            result = subprocess.run([tool, "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                missing.append(tool)

    if missing:
        print(f"Installing missing tools: {', '.join(missing)}")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
    else:
        print("All linting/formatter tools are installed.")

def main() -> None:
    """Main entry point for setup_linting."""
    parser = argparse.ArgumentParser(description="Setup linting and formatting tools")
    parser.add_argument("--force", action="store_true", help="Force recreation of config files")
    args = parser.parse_args()

    print("Setting up linting and formatting configuration...")

    # Install tools
    install_linting_tools()

    # Create/Update configs
    if not validate_ruff_config()[0] or args.force:
        create_ruff_config()
    
    if not validate_pyproject_black()[0] or args.force:
        create_black_config()
    
    if not validate_flake8_config()[0] or args.force:
        create_flake8_config()

    print("Linting and formatting setup complete.")
    print("Run 'ruff check .' to check code.")
    print("Run 'black .' to format code.")
    print("Run 'flake8 .' to run flake8 checks.")

if __name__ == "__main__":
    main()