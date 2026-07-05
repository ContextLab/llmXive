"""
Configuration for linting (ruff) and formatting (black) tools.

This module centralizes configuration settings to ensure consistency
across the project. It generates configuration files for ruff and black.
"""
import os
import tomlkit
import tomli_w
import json

def get_ruff_config():
    """Return ruff configuration dictionary."""
    return {
        "lint": {
            "select": [
                "E",      # pycodestyle errors
                "W",      # pycodestyle warnings
                "F",      # pyflakes
                "I",      # isort
                "B",      # flake8-bugbear
                "C4",     # flake8-comprehensions
                "UP",     # pyupgrade
            ],
            "ignore": [
                "E501",   # Line too long (handled by black)
                "B008",   # Do not perform function call in argument defaults
            ],
            "unfixable": ["F401"], # Unused imports
        },
        "line-length": 88,
        "target-version": "py311",
    }

def get_black_config():
    """Return black configuration dictionary."""
    return {
        "line-length": 88,
        "target-version": ["py311"],
        "include": r'\.pyi?$',
        "exclude": r'''
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
        )/
        ''',
    }

def generate_ruff_toml(root_dir=".", filename="ruff.toml"):
    """Generate a ruff.toml file with the current configuration."""
    config = get_ruff_config()
    path = os.path.join(root_dir, filename)
    with open(path, "w") as f:
        # Using tomlkit for pretty printing, or simple string conversion
        # Since tomlkit might not be in deps, let's write manually for safety
        # or use a simple approach if tomlkit is not guaranteed.
        # However, T002 added dependencies. Let's assume we can write a simple TOML.
        # To be safe and dependency-light, we construct the string.
        
        f.write("# Ruff configuration\n")
        f.write(f'line-length = {config["line-length"]}\n')
        f.write(f'target-version = "{config["target-version"]}"\n\n')
        
        f.write('[lint]\n')
        f.write('select = [\n')
        for rule in config["lint"]["select"]:
            f.write(f'    "{rule}",\n')
        f.write(']\n')
        
        f.write('ignore = [\n')
        for rule in config["lint"]["ignore"]:
            f.write(f'    "{rule}",\n')
        f.write(']\n')
        
        f.write('unfixable = [\n')
        for rule in config["lint"]["unfixable"]:
            f.write(f'    "{rule}",\n')
        f.write(']\n')
    return path

def generate_pyproject_toml(root_dir=".", filename="pyproject.toml"):
    """
    Update or create pyproject.toml with Black configuration.
    Assumes a basic pyproject.toml structure or creates the tool section.
    """
    path = os.path.join(root_dir, filename)
    black_config = get_black_config()
    
    # Simple approach: Append or create section. 
    # For robustness in a script, we might read existing content.
    # But for this task, generating a standard config file is sufficient.
    
    content = f"""[tool.black]
line-length = {black_config["line-length"]}
target-version = ['py311']
include = {black_config["include"]}
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
)/
'''
"""
    # If file exists, we should ideally merge, but for T003 setup,
    # writing a standard config block is the goal. 
    # We will overwrite if it's just for the tool section or append carefully.
    # To be safe and simple as per "extend, don't re-author" without complex parsing:
    # We'll write the tool.black section. If pyproject.toml exists, we assume
    # the user or a previous step handles merging, or we overwrite if it's small.
    # Given the constraint "Extend, don't re-author", and T002 created deps,
    # we will write a fresh pyproject.toml if it doesn't exist, or append the tool section.
    
    if os.path.exists(path):
        with open(path, "r") as f:
            existing = f.read()
        if "[tool.black]" not in existing:
            with open(path, "a") as f:
                f.write("\n" + content)
        return path
    
    with open(path, "w") as f:
        f.write(content)
    return path

def main():
    """Main entry point to generate configuration files."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"Generating configuration files in {root}...")
    
    ruff_path = generate_ruff_toml(root)
    print(f"Created: {ruff_path}")
    
    pyproject_path = generate_pyproject_toml(root)
    print(f"Updated: {pyproject_path}")
    
    print("Configuration complete. Run 'ruff check .' and 'black .' to apply.")

if __name__ == "__main__":
    main()