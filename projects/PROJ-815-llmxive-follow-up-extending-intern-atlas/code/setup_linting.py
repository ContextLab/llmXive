"""
Setup script for linting (ruff) and formatting (black) tools.
This script creates configuration files and ensures dependencies are present.
"""
import os
import sys
from pathlib import Path

# Ensure we can import from the code directory
code_root = Path(__file__).parent
project_root = code_root.parent

def ensure_ruff_config():
    """Create a .ruff.toml configuration file."""
    config_path = project_root / ".ruff.toml"
    
    if config_path.exists():
        print(f"[INFO] {config_path} already exists. Skipping creation.")
        return True

    config_content = """# Ruff configuration for llmXive project
target-version = "py311"

[lint]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "SIM", # flake8-simplify
    "ARG", # flake8-unused-arguments
    "PTH", # flake8-use-pathlib
]
ignore = [
    "E501", # Line too long (handled by Black)
    "B008", # Do not perform function call in argument defaults (common in fastapi/pytest)
    "ARG001", # Unused function arguments (sometimes needed for interface compatibility)
]

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# Exclude a few directories.
extend-exclude = [
    "__pycache__",
    "data/raw",
    "data/cache",
    ".git",
    "venv",
    ".venv",
]

# Same as Black.
line-length = 88

[lint.per-file-ignores]
# Ignore unused imports in __init__.py files
"__init__.py" = ["F401"]
# Ignore specific rules in test files if needed
"tests/**/*.py" = ["ARG001", "S101"]
"""
    
    try:
        config_path.write_text(config_content, encoding="utf-8")
        print(f"[SUCCESS] Created {config_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create {config_path}: {e}")
        return False

def ensure_black_config():
    """Create a pyproject.toml with Black configuration if not present, or update it."""
    config_path = project_root / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
skip-string-normalization = false
exclude = '''
/(
    \.git
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
    | data/raw
    | data/cache
)/
'''
"""

    if not config_path.exists():
        try:
            config_path.write_text(black_section, encoding="utf-8")
            print(f"[SUCCESS] Created {config_path} with Black configuration.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to create {config_path}: {e}")
            return False
    
    # If it exists, check if [tool.black] is already there
    content = config_path.read_text(encoding="utf-8")
    if "[tool.black]" in content:
        print(f"[INFO] {config_path} already contains [tool.black] section. Skipping update.")
        return True
    
    # Append the black section
    try:
        with open(config_path, "a", encoding="utf-8") as f:
            f.write(black_section)
        print(f"[SUCCESS] Appended Black configuration to {config_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update {config_path}: {e}")
        return False

def update_requirements():
    """Ensure ruff and black are in requirements.txt."""
    req_path = project_root / "code" / "requirements.txt"
    
    if not req_path.exists():
        print(f"[WARNING] {req_path} not found. Cannot update requirements.")
        return False

    content = req_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    has_ruff = any("ruff" in line.lower() for line in lines)
    has_black = any("black" in line.lower() for line in lines)
    
    new_lines = []
    for line in lines:
        new_lines.append(line)
    
    if not has_ruff:
        new_lines.append("ruff>=0.1.0")
        print("[INFO] Added 'ruff' to requirements.txt")
    
    if not has_black:
        new_lines.append("black>=23.0.0")
        print("[INFO] Added 'black' to requirements.txt")
    
    if not has_ruff or not has_black:
        try:
            req_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            print(f"[SUCCESS] Updated {req_path}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to update {req_path}: {e}")
            return False
    
    print(f"[INFO] {req_path} already contains ruff and black.")
    return True

def main():
    """Main entry point for setup_linting."""
    print("=== Setting up Linting and Formatting Tools ===")
    
    success = True
    
    # 1. Update requirements.txt
    if not update_requirements():
        success = False
    
    # 2. Create .ruff.toml
    if not ensure_ruff_config():
        success = False
    
    # 3. Update pyproject.toml for Black
    if not ensure_black_config():
        success = False
    
    if success:
        print("\n=== Setup Complete ===")
        print("You can now run:")
        print("  ruff check .")
        print("  black .")
        print("  ruff check . --fix")
        print("  black . --check")
    else:
        print("\n=== Setup Failed ===")
        sys.exit(1)

if __name__ == "__main__":
    main()