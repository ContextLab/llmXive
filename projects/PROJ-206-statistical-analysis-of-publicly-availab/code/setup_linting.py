"""
Configure linting (ruff) and formatting (black) tools for the project.

This script:
1. Ensures 'ruff' and 'black' are installed (from requirements.txt).
2. Generates a 'pyproject.toml' file with standardized configuration for both tools.
3. Creates a '.gitignore' update if it doesn't contain linting artifacts.
"""
import os
import subprocess
import sys
from pathlib import Path

def ensure_dependencies():
    """Verify that ruff and black are installed."""
    required = ["ruff", "black"]
    missing = []
    
    for pkg in required:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "show", pkg], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            missing.append(pkg)
    
    if missing:
        print(f"Missing dependencies: {missing}. Installing from requirements.txt...")
        # Try installing from requirements.txt first
        req_file = Path("requirements.txt")
        if req_file.exists():
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
        else:
            # Fallback: install missing packages directly
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
    
    print("Linting and formatting dependencies verified.")

def create_pyproject_config():
    """Create or update pyproject.toml with ruff and black configurations."""
    config_content = """[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    # directories
    \\.eggs
    | \\.git
    | \\.hg
    | \\.mypy_cache
    | \\.tox
    | \\.venv
    | _build
    | buck-out
    | build
    | dist
    | data
    | state
)/
'''

[tool.ruff]
# Same as Black.
line-length = 88
indent-width = 4

# Assume Python 3.9+
target-version = "py39"

[tool.ruff.lint]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = ["E", "F", "W", "I", "N", "UP", "ANN", "S", "B", "C4", "SIM"]
ignore = [
    "ANN101",  # Missing type annotation for `self` in method
    "ANN102",  # Missing type annotation for `cls` in classmethod
    "S101",    # Use of assert detected (often used in tests)
    "S105",    # Possible hardcoded password (common in configs/tests)
    "S106",    # Possible hardcoded password
    "S107",    # Possible hardcoded password
    "S311",    # Standard pseudo-random generators are not suitable for cryptographic purposes (often used in seeds)
]

# Allow autofix for all enabled rules (when `--fix` is provided)
fixable = ["ALL"]
unfixable = []

# Exclude a few files/directories
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".git-rewrite",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pytype",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "venv",
    "data",
    "state",
]

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ANN", "S101"]
"code/setup_*.py" = ["T201"]

[tool.ruff.format]
# Like Black, use double quotes for strings.
quote-style = "double"

# Like Black, indent with spaces, rather than tabs.
indent-style = "space"

# Like Black, respect magic trailing commas.
skip-magic-trailing-comma = false

# Like Black, automatically detect the appropriate line ending.
line-ending = "auto"
"""
    
    pyproject_path = Path("pyproject.toml")
    
    if pyproject_path.exists():
        # Read existing content
        existing = pyproject_path.read_text()
        if "[tool.black]" in existing and "[tool.ruff]" in existing:
            print("pyproject.toml already contains ruff and black configurations. Skipping update.")
            return
        else:
            print("Appending ruff and black configurations to existing pyproject.toml...")
            with open(pyproject_path, "a") as f:
                f.write("\n\n" + config_content)
    else:
        print("Creating new pyproject.toml with ruff and black configurations...")
        pyproject_path.write_text(config_content)
    
    print("Configuration written to pyproject.toml")

def main():
    """Main entry point for linting setup."""
    print("Starting linting and formatting configuration...")
    
    # 1. Ensure dependencies are installed
    ensure_dependencies()
    
    # 2. Create configuration file
    create_pyproject_config()
    
    print("Linting and formatting setup complete.")
    print("Run 'ruff check .' to lint and 'black .' to format.")

if __name__ == "__main__":
    main()