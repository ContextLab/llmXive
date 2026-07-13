import os
import sys
from pathlib import Path
import json

def update_requirements():
    """
    Adds ruff and black to requirements.txt if not present.
    """
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        print("Error: requirements.txt not found. Run T002 first.")
        return False

    lines = requirements_path.read_text().splitlines()
    existing_packages = {line.split("==")[0].lower().split("[")[0] for line in lines if line.strip() and not line.startswith("#")}

    packages_to_add = [
        "ruff>=0.1.0",
        "black>=23.0.0"
    ]

    updated = False
    new_lines = []
    for line in lines:
        new_lines.append(line)
        pkg_name = line.split("==")[0].lower().split("[")[0] if "==" in line else line.lower().split("[")[0]
        if pkg_name.strip() and pkg_name not in existing_packages:
            pass # Already checked against set, but we need to handle the case where we are iterating and adding
        
    # Re-evaluate: simply append missing packages
    current_packages = {line.split("==")[0].strip().lower() for line in lines if "==" in line}
    
    for pkg in packages_to_add:
        pkg_name = pkg.split("==")[0].split(">=")[0].split("<")[0].strip()
        if pkg_name.lower() not in current_packages:
            new_lines.append(pkg)
            updated = True

    if updated:
        requirements_path.write_text("\n".join(new_lines) + "\n")
        print(f"Updated requirements.txt with: {packages_to_add}")
    else:
        print("requirements.txt already up to date.")
    return True

def create_ruff_config():
    """
    Creates a .ruff.toml configuration file.
    """
    config_path = Path(".ruff.toml")
    if config_path.exists():
        print(".ruff.toml already exists.")
        return True

    config_content = """
# Ruff configuration for llmXive
target-version = "py310"

[lint]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = ["E", "F", "W", "I", "N", "UP", "ANN", "S", "B", "C4", "SIM"]
ignore = ["ANN101", "ANN102", "S101"]

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# A list of file names to exclude from linting.
extend-exclude = ["data/", "build/", "dist/", ".venv/"]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[lint.isort]
known-first-party = ["utils", "scheduler", "training", "analysis"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    config_path.write_text(config_content.strip() + "\n")
    print("Created .ruff.toml")
    return True

def create_black_config():
    """
    Creates a pyproject.toml with Black configuration if not present,
    or appends to existing [tool.black] section.
    """
    pyproject_path = Path("pyproject.toml")
    
    content = ""
    if pyproject_path.exists():
        content = pyproject_path.read_text()
    
    if "[tool.black]" in content:
        print("[tool.black] section already exists in pyproject.toml")
        return True

    black_section = """
[tool.black]
line-length = 88
target-version = ['py310']
include = '\\.pyi?$'
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
  | data
)/
'''
"""
    
    if content:
        content += "\n" + black_section
    else:
        content = black_section

    pyproject_path.write_text(content)
    print("Updated pyproject.toml with Black configuration")
    return True

def main():
    """
    Main entry point to configure linting and formatting tools.
    """
    print("Configuring Linting and Formatting tools...")
    
    success = True
    
    # 1. Update requirements.txt
    if not update_requirements():
        success = False
    
    # 2. Create Ruff config
    if not create_ruff_config():
        success = False
        
    # 3. Create Black config
    if not create_black_config():
        success = False
        
    if success:
        print("\nLinting and Formatting configuration complete.")
        print("Run 'ruff check .' to lint and 'black .' to format.")
    else:
        print("\nConfiguration failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()