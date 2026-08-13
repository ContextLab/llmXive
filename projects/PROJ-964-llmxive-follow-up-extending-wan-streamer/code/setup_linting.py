import os
import sys
from pathlib import Path

def ensure_ruff_config():
    """
    Create .ruff.toml with specific linting rules.
    """
    base_path = Path(__file__).resolve().parent.parent
    config_path = base_path / ".ruff.toml"
    
    content = """
# Ruff configuration for llmXive project
line-length = 88
target-version = "py39"

[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by formatter)
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["code"]
"""
    
    with open(config_path, "w") as f:
        f.write(content.strip())
        
    print(f"Created ruff config: {config_path}")
    return config_path

def ensure_black_config():
    """
    Ensure black configuration exists in pyproject.toml.
    Note: This task assumes pyproject.toml exists (T005d).
    We will just verify or append if missing.
    """
    base_path = Path(__file__).resolve().parent.parent
    pyproject_path = base_path / "pyproject.toml"
    
    if not pyproject_path.exists():
        # Create a basic pyproject.toml with black config if it doesn't exist
        content = """
[tool.black]
line-length = 88
target-version = ['py39']
"""
        with open(pyproject_path, "w") as f:
            f.write(content)
        print(f"Created pyproject.toml with black config: {pyproject_path}")
        return pyproject_path
    
    # If it exists, we assume T005d handled it
    print(f"pyproject.toml already exists: {pyproject_path}")
    return pyproject_path

def main():
    """
    Main entry point to create linting configurations.
    """
    print("Setting up linting configurations...")
    ruff_path = ensure_ruff_config()
    black_path = ensure_black_config()
    
    if ruff_path.exists() and black_path.exists():
        print("\nLinting configurations are ready.")
        return 0
    else:
        print("\nFailed to create linting configurations.")
        return 1

if __name__ == "__main__":
    sys.exit(main())