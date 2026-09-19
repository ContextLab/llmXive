"""
setup_linting.py
Implements T003: Configure linting (ruff) and formatting (black) tools.

This script ensures the necessary configuration files (.ruff.toml, pyproject.toml)
are present and correctly configured for the project. It also verifies
that the required dev dependencies (black, ruff) are listed in requirements.txt.
"""
import os
import sys
from pathlib import Path

def ensure_requirements_entry():
    """Ensures ruff and black are listed in requirements.txt."""
    req_path = Path("requirements.txt")
    if not req_path.exists():
        print("Warning: requirements.txt not found. Creating it.")
        req_path.write_text("# Project dependencies\n")

    content = req_path.read_text()
    if "ruff" not in content:
        req_path.write_text(content + "ruff>=0.1.0,<0.2.0\n")
        print("Added 'ruff' to requirements.txt")
    
    if "black" not in content:
        req_path.write_text(content + "black>=23.0.0,<24.0.0\n")
        print("Added 'black' to requirements.txt")

def install_dev_dependencies():
    """Installs dev dependencies if pip is available."""
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "ruff", "black"])
        print("Successfully installed ruff and black.")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to install dependencies automatically: {e}")
        print("Please run: pip install ruff black")

def write_ruff_config():
    """Creates .ruff.toml if it doesn't exist."""
    config_path = Path(".ruff.toml")
    if config_path.exists():
        print(f"{config_path} already exists. Skipping creation.")
        return

    config_content = """# Ruff configuration for llmXive project
[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501", "B008", "SIM105"]
fixable = ["ALL"]
unfixable = []
exclude = [
    ".bzr", ".direnv", ".eggs", ".git", ".git-rewrite", ".hg", ".mypy_cache",
    ".nox", ".pants.d", ".pytype", ".ruff_cache", ".svn", ".tox", ".venv",
    "__pypackages__", "_build", "buck-out", "build", "dist", "node_modules", "venv",
]
target-version = "py311"

[lint.mccabe]
max-complexity = 15

[lint.isort]
lines-after-imports = 2
known-first-party = ["src", "tests", "setup_data_dirs", "setup_env_limits", "setup_linting", "setup_model_cache", "setup_python_env", "setup_source_dirs"]
"""
    config_path.write_text(config_content)
    print(f"Created {config_path}")

def write_black_config():
    """Ensures Black configuration exists in pyproject.toml."""
    config_path = Path("pyproject.toml")
    if not config_path.exists():
        config_path.write_text("[project]\nname = 'llmxive-research'\n")
    
    content = config_path.read_text()
    if "[tool.black]" not in content:
        black_section = """
[tool.black]
line-length = 100
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
        config_path.write_text(content + black_section)
        print("Added [tool.black] section to pyproject.toml")
    else:
        print("Black configuration already present in pyproject.toml")

def main():
    """Main entry point for T003 implementation."""
    print("Starting T003: Configure linting (ruff) and formatting (black) tools...")
    
    ensure_requirements_entry()
    write_ruff_config()
    write_black_config()
    
    # Attempt installation
    install_dev_dependencies()
    
    print("T003 Configuration complete.")

if __name__ == "__main__":
    main()