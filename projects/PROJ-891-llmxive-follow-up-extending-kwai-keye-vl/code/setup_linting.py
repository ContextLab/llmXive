import os
import sys
import subprocess
from pathlib import Path

def ensure_requirements_entry():
    """Ensure ruff and black are listed in requirements.txt."""
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        raise FileNotFoundError("requirements.txt not found in project root.")
    
    content = requirements_path.read_text()
    lines = content.splitlines()
    
    # Check for existing entries
    has_ruff = any("ruff" in line for line in lines)
    has_black = any("black" in line for line in lines)
    
    new_lines = []
    if not has_ruff:
        new_lines.append("ruff>=0.1.0")
    if not has_black:
        new_lines.append("black>=23.0.0")
    
    if new_lines:
        with open(requirements_path, "a") as f:
            f.write("\n" + "\n".join(new_lines) + "\n")
        print("Updated requirements.txt with linting dependencies.")
    else:
        print("Linting dependencies already present in requirements.txt.")

def install_dev_dependencies():
    """Install ruff and black if not already installed."""
    try:
        import ruff
        import black
        print("Linting tools already installed.")
        return
    except ImportError:
        pass

    print("Installing linting tools...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
    print("Linting tools installed successfully.")

def write_ruff_config():
    """Create .ruff.toml configuration file."""
    config_path = Path(".ruff.toml")
    if config_path.exists():
        print(".ruff.toml already exists, skipping creation.")
        return

    config_content = """# Ruff configuration
target-version = "py311"

[lint]
select = [
    "E",  # pyflake errors
    "F",  # pyflake warnings
    "I",  # isort
    "N",  # pep8-naming
    "D",  # pydocstyle
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
    "UP", # py-up
]
ignore = [
    "E501", # Line too long (handled by black)
    "E203", # Whitespace before ':'
    "W292", # No newline at end of file (handled by black)
]

[lint.per-file-ignores]
"tests/*" = ["S101"] # Allow asserts in tests

[lint.isort]
known-first-party = ["src", "tests", "scripts"]
"""
    config_path.write_text(config_content)
    print("Created .ruff.toml configuration.")

def write_black_config():
    """Create pyproject.toml section for Black if not present."""
    pyproject_path = Path("pyproject.toml")
    
    if not pyproject_path.exists():
        pyproject_path.write_text("""[tool.black]
line-length = 88
target-version = ['py311']
exclude = [
    "\\.git",
    "\\.venv",
    "__pycache__",
    "dist",
    "build",
]
""")
        print("Created pyproject.toml with Black configuration.")
        return

    content = pyproject_path.read_text()
    if "[tool.black]" in content:
        print("Black configuration already present in pyproject.toml.")
        return

    # Append configuration
    new_config = """
[tool.black]
line-length = 88
target-version = ['py311']
exclude = [
    "\\.git",
    "\\.venv",
    "__pycache__",
    "dist",
    "build",
]
"""
    with open(pyproject_path, "a") as f:
        f.write(new_config)
    print("Added Black configuration to pyproject.toml.")

def main():
    """Main entry point for linting setup."""
    print("Setting up linting (ruff) and formatting (black)...")
    
    # Ensure dependencies
    ensure_requirements_entry()
    install_dev_dependencies()
    
    # Write configuration files
    write_ruff_config()
    write_black_config()
    
    print("Linting and formatting setup complete.")
    print("To run checks: ruff check .")
    print("To format code: black .")
    print("To auto-fix: ruff check . --fix")

if __name__ == "__main__":
    main()