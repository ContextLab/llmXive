import os
import subprocess
import sys
import json
from pathlib import Path

def run_command(cmd: list) -> bool:
    """Execute a shell command and return True if successful."""
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return False

def update_requirements() -> bool:
    """Ensure black and ruff are added to requirements.txt."""
    req_path = Path("requirements.txt")
    if not req_path.exists():
        print("requirements.txt not found. Please run T002 first.")
        return False

    lines = req_path.read_text().splitlines()
    required_packages = ["black>=23.0.0", "ruff>=0.1.0"]
    updated = False

    with open(req_path, "w") as f:
        for line in lines:
            f.write(line + "\n")
            # Check if package is missing (simple string match for version start)
            for pkg in required_packages:
                pkg_name = pkg.split(">=")[0]
                if not any(line.strip().startswith(pkg_name) for line in lines):
                    if line.strip() == lines[-1]: # If we are at the end
                        pass 
    
    # Re-read to check existence properly
    content = req_path.read_text()
    for pkg in required_packages:
        pkg_name = pkg.split(">=")[0]
        if pkg_name not in content:
            with open(req_path, "a") as f:
                f.write(pkg + "\n")
            updated = True
            print(f"Added {pkg} to requirements.txt")
    
    if not updated:
        print("black and ruff are already in requirements.txt")
    return True

def create_pyproject_toml() -> bool:
    """Create pyproject.toml with black and ruff configuration."""
    config = {
        "tool": {
            "black": {
                "line-length": 88,
                "target-version": ["py311"],
                "include": "\\.pyi?$",
                "exclude": "/(\\.git|\\.hg|\\.mypy_cache|\\.tox|\\.venv|_build|buck-out|build|dist)/"
            },
            "ruff": {
                "line-length": 88,
                "target-version": "py311",
                "select": [
                    "E", "W",  # pycodestyle
                    "F",       # Pyflakes
                    "I",       # isort
                    "N",       # pep8-naming
                    "UP",      # pyupgrade
                    "B",       # flake8-bugbear
                    "C4",      # flake8-comprehensions
                    "SIM",     # flake8-simplify
                ],
                "ignore": [],
                "exclude": [
                    ".git",
                    ".mypy_cache",
                    ".tox",
                    ".venv",
                    "build",
                    "dist",
                ],
                "per-file-ignores": {
                    "__init__.py": ["F401"]
                }
            }
        }
    }

    toml_path = Path("pyproject.toml")
    if toml_path.exists():
        print("pyproject.toml already exists. Updating configuration...")
        # Simple append strategy for safety, or overwrite if it's just config
        # For this task, we will overwrite to ensure correct config
        pass

    with open(toml_path, "w") as f:
        f.write("[tool.black]\n")
        f.write('line-length = 88\n')
        f.write('target-version = ["py311"]\n')
        f.write('include = "\\\\.pyi?$"\n')
        f.write('exclude = "/(\\\\.git|\\\\.hg|\\\\.mypy_cache|\\\\.tox|\\\\.venv|_build|buck-out|build|dist)/"\n')
        f.write("\n")
        f.write("[tool.ruff]\n")
        f.write('line-length = 88\n')
        f.write('target-version = "py311"\n')
        f.write('select = [\n')
        f.write('    "E", "W",\n')
        f.write('    "F",\n')
        f.write('    "I",\n')
        f.write('    "N",\n')
        f.write('    "UP",\n')
        f.write('    "B",\n')
        f.write('    "C4",\n')
        f.write('    "SIM",\n')
        f.write("]\n")
        f.write('ignore = []\n')
        f.write('exclude = [\n')
        f.write('    ".git",\n')
        f.write('    ".mypy_cache",\n')
        f.write('    ".tox",\n')
        f.write('    ".venv",\n')
        f.write('    "build",\n')
        f.write('    "dist",\n')
        f.write("]\n")
        f.write('per-file-ignores = {\n')
        f.write('    "__init__.py" = ["F401"]\n')
        f.write("}\n")
    
    print(f"Created/Updated {toml_path}")
    return True

def main():
    """Main entry point for setup_linting script."""
    print("Setting up linting (ruff) and formatting (black)...")
    
    # 1. Update requirements.txt
    if not update_requirements():
        print("Failed to update requirements.txt")
        sys.exit(1)
    
    # 2. Create/Update pyproject.toml
    if not create_pyproject_toml():
        print("Failed to create pyproject.toml")
        sys.exit(1)
    
    # 3. Install dependencies
    print("Installing dependencies...")
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]):
        print("Failed to install dependencies")
        sys.exit(1)
    
    # 4. Verify installation
    print("Verifying installation...")
    if not run_command(["black", "--version"]):
        print("Warning: black not found in PATH, but installed via pip. You may need to use 'python -m black'.")
    
    if not run_command(["ruff", "--version"]):
        print("Warning: ruff not found in PATH, but installed via pip. You may need to use 'python -m ruff'.")
    
    print("Linting and formatting setup complete.")

if __name__ == "__main__":
    main()
