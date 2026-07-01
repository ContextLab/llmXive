import os
import sys
from pathlib import Path

def ensure_requirements():
    """
    Ensures the requirements.txt contains necessary linting dependencies.
    Appends them if missing.
    """
    req_file = Path("code/requirements.txt")
    if not req_file.exists():
        req_file.parent.mkdir(parents=True, exist_ok=True)
        req_file.touch()

    with open(req_file, "r") as f:
        content = f.read()

    packages = ["ruff", "black"]
    needs_update = False
    for pkg in packages:
        if pkg not in content:
            needs_update = True
            with open(req_file, "a") as f:
                f.write(f"{pkg}\n")
            print(f"Added {pkg} to requirements.txt")

    if not needs_update:
        print("Linting requirements already present.")

def create_ruff_config():
    """
    Creates a .ruff.toml configuration file with standard settings.
    """
    config_path = Path(".ruff.toml")
    if config_path.exists():
        print("ruff config already exists.")
        return

    config_content = """[lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = []

[lint.per-file-ignores]
"tests/*" = ["S101"]

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
skip-magic-trailing-comma = false
"""
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created {config_path}")

def create_black_config():
    """
    Creates a pyproject.toml with Black configuration if not present.
    """
    config_path = Path("pyproject.toml")
    if not config_path.exists():
        config_path.touch()

    with open(config_path, "r") as f:
        content = f.read()

    black_section = """[tool.black]
line-length = 88
target-version = ['py38']
"""
    
    # Simple check to avoid appending twice
    if "[tool.black]" not in content:
        with open(config_path, "a") as f:
            f.write("\n" + black_section)
        print(f"Updated {config_path} with Black config")
    else:
        print("Black config already present in pyproject.toml")

def main():
    """
    Main entry point to configure linting tools.
    """
    ensure_requirements()
    create_ruff_config()
    create_black_config()
    print("Linting configuration complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())