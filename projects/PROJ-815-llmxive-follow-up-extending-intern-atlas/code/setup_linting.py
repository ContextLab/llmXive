import os
import sys
from pathlib import Path

def ensure_ruff_config():
    """Create .ruff.toml in the code directory if it doesn't exist."""
    root = Path(__file__).resolve().parent
    config_path = root / ".ruff.toml"
    
    if config_path.exists():
        print(f"Ruff config already exists at {config_path}")
        return True
    
    content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.per-file-ignores]
"code/utils/__init__.py" = ["F401"]
"code/data/__init__.py" = ["F401"]
"code/models/__init__.py" = ["F401"]
"code/analysis/__init__.py" = ["F401"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    config_path.write_text(content)
    print(f"Created Ruff config at {config_path}")
    return True

def ensure_black_config():
    """Create .black.toml in the code directory if it doesn't exist."""
    root = Path(__file__).resolve().parent
    config_path = root / ".black.toml"
    
    if config_path.exists():
        print(f"Black config already exists at {config_path}")
        return True
    
    content = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
    | \\.hg
    | \\.mypy_cache
    | \\.tox
    | \\.venv
    | _build
    | buck-out
    | build
    | dist
)/
'''
"""
    config_path.write_text(content)
    print(f"Created Black config at {config_path}")
    return True

def update_requirements():
    """Ensure ruff and black are in requirements.txt."""
    root = Path(__file__).resolve().parent
    req_path = root / "requirements.txt"
    
    if not req_path.exists():
        print(f"Warning: {req_path} not found. Creating it with linting tools.")
        req_path.write_text("ruff>=0.1.0\nblack>=23.0.0\n")
        return True

    content = req_path.read_text()
    if "ruff" not in content:
        content += "\nruff>=0.1.0"
    if "black" not in content:
        content += "\nblack>=23.0.0"
    
    req_path.write_text(content)
    print(f"Updated {req_path} with linting tools")
    return True

def main():
    print("Configuring linting and formatting tools...")
    ensure_ruff_config()
    ensure_black_config()
    update_requirements()
    print("Linting and formatting configuration complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())