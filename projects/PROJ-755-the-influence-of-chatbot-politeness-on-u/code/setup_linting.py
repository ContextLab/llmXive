"""
Setup script to configure linting (ruff/flake8) and formatting (black) for the project.
Creates configuration files in the project root:
- pyproject.toml (for black and ruff)
- .flake8 (for flake8, optional fallback)
- .ruff.toml (optional explicit ruff config)

This script is idempotent: it checks for existing configs and validates them,
creating them only if missing or invalid.
"""
import os
import sys
import tomllib
import configparser
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
FLAKE8_PATH = PROJECT_ROOT / ".flake8"
RUFF_PATH = PROJECT_ROOT / ".ruff.toml"

# Default configurations
BLACK_CONFIG = {
    "line-length": 100,
    "target-version": ["py39", "py310", "py311"],
    "include": ["code/**/*.py", "tests/**/*.py"],
    "exclude": [".git", "__pycache__", "data", "venv", ".venv"],
    "skip-string-normalization": False,
    "preview": True,
}

RUFF_CONFIG = {
    "line-length": 100,
    "target-version": "py39",
    "select": [
        "E",   # pycodestyle errors
        "W",   # pycodestyle warnings
        "F",   # Pyflakes
        "I",   # isort
        "B",   # flake8-bugbear
        "C4",  # flake8-comprehensions
        "UP",  # pyupgrade
        "N",   # pep8-naming
        "RUF", # ruff-specific rules
    ],
    "ignore": [
        "E501", # line too long (handled by black)
        "B008", # do not perform function calls in argument defaults (common in ML)
        "RUF012", # mutable default values in class attributes (often needed for dataclasses)
    ],
    "exclude": [
        ".git",
        "__pycache__",
        "data",
        "venv",
        ".venv",
        "build",
        "dist",
    ],
    "per-file-ignores": {
        "__init__.py": ["F401"], # allow unused imports in init files
    },
    "isort": {
        "known-first-party": ["utils"],
        "force-single-line": False,
        "order-by-type": True,
    },
}

FLAKE8_CONFIG = {
    "max-line-length": 100,
    "exclude": ".git,__pycache__,data,venv,.venv,build,dist",
    "ignore": "E501,W503", # line length handled by black, W503 conflict with black
}

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and return True if it does."""
    if path.exists():
        print(f"[OK] {description} exists: {path}")
        return True
    print(f"[MISSING] {description} not found: {path}")
    return False

def validate_ruff_config() -> Tuple[bool, Optional[str]]:
    """Validate .ruff.toml or [tool.ruff] in pyproject.toml."""
    # Check .ruff.toml first
    if RUFF_PATH.exists():
        try:
            # Basic validation: try to load as TOML
            with open(RUFF_PATH, "rb") as f:
                tomllib.load(f)
            print("[OK] .ruff.toml is valid TOML")
            return True, None
        except Exception as e:
            return False, f".ruff.toml is invalid TOML: {e}"
    
    # Check pyproject.toml for [tool.ruff]
    if PYPROJECT_PATH.exists():
        try:
            with open(PYPROJECT_PATH, "rb") as f:
                content = tomllib.load(f)
            if "tool" in content and "ruff" in content["tool"]:
                print("[OK] pyproject.toml contains [tool.ruff]")
                return True, None
        except Exception as e:
            return False, f"pyproject.toml is invalid or missing [tool.ruff]: {e}"
    
    return False, "No ruff configuration found"

def validate_pyproject_black() -> Tuple[bool, Optional[str]]:
    """Validate [tool.black] in pyproject.toml."""
    if not PYPROJECT_PATH.exists():
        return False, "pyproject.toml does not exist"
    
    try:
        with open(PYPROJECT_PATH, "rb") as f:
            content = tomllib.load(f)
        if "tool" in content and "black" in content["tool"]:
            print("[OK] pyproject.toml contains [tool.black]")
            return True, None
        return False, "pyproject.toml missing [tool.black] section"
    except Exception as e:
        return False, f"Error reading pyproject.toml: {e}"

def validate_flake8_config() -> Tuple[bool, Optional[str]]:
    """Validate .flake8 or setup.cfg for flake8 config."""
    if FLAKE8_PATH.exists():
        try:
            config = configparser.ConfigParser()
            config.read(FLAKE8_PATH)
            if "flake8" in config:
                print("[OK] .flake8 exists and contains [flake8]")
                return True, None
            return False, ".flake8 exists but missing [flake8] section"
        except Exception as e:
            return False, f"Error reading .flake8: {e}"
    
    # Check setup.cfg as fallback
    setup_cfg = PROJECT_ROOT / "setup.cfg"
    if setup_cfg.exists():
        try:
            config = configparser.ConfigParser()
            config.read(setup_cfg)
            if "flake8" in config:
                print("[OK] setup.cfg contains [flake8]")
                return True, None
        except Exception as e:
            return False, f"Error reading setup.cfg: {e}"
    
    return False, "No flake8 configuration found"

def create_ruff_config() -> None:
    """Create a default .ruff.toml configuration file."""
    import tomli_w
    
    config_content = {
        "line-length": RUFF_CONFIG["line-length"],
        "target-version": RUFF_CONFIG["target-version"],
        "select": RUFF_CONFIG["select"],
        "ignore": RUFF_CONFIG["ignore"],
        "exclude": RUFF_CONFIG["exclude"],
        "per-file-ignores": RUFF_CONFIG["per-file-ignores"],
        "isort": RUFF_CONFIG["isort"],
    }
    
    with open(RUFF_PATH, "wb") as f:
        tomli_w.dump(config_content, f)
    print(f"[CREATED] {RUFF_PATH}")

def create_black_config() -> None:
    """Create or update [tool.black] in pyproject.toml."""
    import tomli_w
    
    if PYPROJECT_PATH.exists():
        with open(PYPROJECT_PATH, "rb") as f:
            content = tomli.load(f)
    else:
        content = {}
    
    if "tool" not in content:
        content["tool"] = {}
    
    content["tool"]["black"] = {
        "line-length": BLACK_CONFIG["line-length"],
        "target-version": BLACK_CONFIG["target-version"],
        "include": BLACK_CONFIG["include"],
        "exclude": BLACK_CONFIG["exclude"],
        "skip-string-normalization": BLACK_CONFIG["skip-string-normalization"],
        "preview": BLACK_CONFIG["preview"],
    }
    
    with open(PYPROJECT_PATH, "wb") as f:
        tomli_w.dump(content, f)
    print(f"[UPDATED] {PYPROJECT_PATH} with [tool.black]")

def create_flake8_config() -> None:
    """Create a default .flake8 configuration file."""
    config = configparser.ConfigParser()
    config["flake8"] = {
        "max-line-length": str(FLAKE8_CONFIG["max-line-length"]),
        "exclude": FLAKE8_CONFIG["exclude"],
        "ignore": FLAKE8_CONFIG["ignore"],
    }
    
    with open(FLAKE8_PATH, "w") as f:
        config.write(f)
    print(f"[CREATED] {FLAKE8_PATH}")

def install_linting_tools() -> None:
    """Print instructions to install linting tools."""
    print("\n" + "="*60)
    print("INSTALLATION INSTRUCTIONS")
    print("="*60)
    print("To install the required linting and formatting tools, run:")
    print("  pip install ruff black flake8")
    print("\nOr add them to your requirements.txt:")
    print("  ruff")
    print("  black")
    print("  flake8")
    print("="*60 + "\n")

def main() -> int:
    """Main entry point for the setup script."""
    parser = argparse.ArgumentParser(
        description="Setup linting (ruff/flake8) and formatting (black) configurations."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of configuration files even if they exist.",
    )
    args = parser.parse_args()

    print(f"Project root: {PROJECT_ROOT}")
    print("-" * 60)

    # Check and create Ruff config
    ruff_valid, ruff_err = validate_ruff_config()
    if not ruff_valid or args.force:
        print(f"[ACTION] Creating/Updating Ruff config: {ruff_err}")
        create_ruff_config()

    # Check and create Black config
    black_valid, black_err = validate_pyproject_black()
    if not black_valid or args.force:
        print(f"[ACTION] Creating/Updating Black config: {black_err}")
        create_black_config()

    # Check and create Flake8 config
    flake8_valid, flake8_err = validate_flake8_config()
    if not flake8_valid or args.force:
        print(f"[ACTION] Creating/Updating Flake8 config: {flake8_err}")
        create_flake8_config()

    # Final validation
    print("-" * 60)
    print("Final Validation:")
    
    checks = [
        ("Ruff", validate_ruff_config()),
        ("Black", validate_pyproject_black()),
        ("Flake8", validate_flake8_config()),
    ]
    
    all_valid = True
    for name, (valid, err) in checks:
        if valid:
            print(f"  [OK] {name}")
        else:
            print(f"  [FAIL] {name}: {err}")
            all_valid = False

    install_linting_tools()

    if all_valid:
        print("\n[SUCCESS] All linting and formatting configurations are ready.")
        return 0
    else:
        print("\n[WARNING] Some configurations could not be validated.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
