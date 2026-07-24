import os
import sys
from pathlib import Path
import subprocess

def ensure_requirements():
    """Ensure linting and formatting tools are available."""
    try:
        import ruff
        import black
        import flake8
        return True
    except ImportError:
        print("Installing linting tools...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black", "flake8"])
            return True
        except subprocess.CalledProcessError:
            print("Failed to install linting tools. Please install manually: pip install ruff black flake8")
            return False

def create_ruff_config(root: Path):
    """Create ruff.toml configuration."""
    config_content = """# Ruff configuration
[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[lint.isort]
known-first-party = ["code", "tests"]

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
"""
    config_path = root / "ruff.toml"
    config_path.write_text(config_content)
    print(f"Created ruff configuration: {config_path}")

def create_black_config(root: Path):
    """Create pyproject.toml with black configuration."""
    config_path = root / "pyproject.toml"
    if config_path.exists():
        content = config_path.read_text()
        if "[tool.black]" not in content:
            content += "\n[tool.black]\nline-length = 88\ntarget-version = ['py39']\n"
            config_path.write_text(content)
            print(f"Updated pyproject.toml with black configuration: {config_path}")
        else:
            print(f"Black configuration already exists in {config_path}")
    else:
        config_content = """[tool.black]
line-length = 88
target-version = ['py39']
"""
        config_path.write_text(config_content)
        print(f"Created pyproject.toml with black configuration: {config_path}")

def create_flake8_config(root: Path):
    """Create .flake8 configuration."""
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, E501
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs
"""
    config_path = root / ".flake8"
    config_path.write_text(config_content)
    print(f"Created flake8 configuration: {config_path}")

def main():
    """Setup linting and formatting tools."""
    root = Path(__file__).resolve().parent.parent
    
    if not ensure_requirements():
        return 1
    
    create_ruff_config(root)
    create_black_config(root)
    create_flake8_config(root)
    
    print("Linting and formatting tools configured successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())