import subprocess
import sys
import os
from pathlib import Path

def ensure_package_installed(package_name: str, pip_name: str = None) -> bool:
    """
    Ensure a package is installed in the current environment.
    Returns True if installed, False otherwise.
    """
    if pip_name is None:
        pip_name = package_name
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def create_ruff_config() -> None:
    """
    Create a minimal ruff.toml configuration file in the project root.
    """
    ruff_config_content = """
[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # line too long (handled by black)
]

[lint.isort]
known-first-party = ["src"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "ruff.toml"
    
    with open(config_path, 'w') as f:
        f.write(ruff_config_content.strip())
    
    print(f"Created ruff configuration at: {config_path}")

def create_pyproject_config() -> None:
    """
    Create/update pyproject.toml with black configuration.
    """
    root_dir = Path(__file__).parent.parent
    pyproject_path = root_dir / "pyproject.toml"
    
    black_config = """
[tool.black]
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
    
    if pyproject_path.exists():
        # Read existing content
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        # Check if [tool.black] section already exists
        if "[tool.black]" not in content:
            content += "\n" + black_config
            with open(pyproject_path, 'w') as f:
                f.write(content)
            print(f"Updated pyproject.toml with black configuration")
        else:
            print("Black configuration already exists in pyproject.toml")
    else:
        with open(pyproject_path, 'w') as f:
            f.write(black_config.strip())
        print(f"Created pyproject.toml with black configuration at: {pyproject_path}")

def main() -> None:
    """
    Main entry point to configure linting and formatting tools.
    """
    print("Configuring linting (ruff) and formatting (black) tools...")
    
    # Ensure packages are installed
    print("Checking/installing ruff...")
    if not ensure_package_installed("ruff", "ruff"):
        print("ERROR: Failed to install ruff")
        sys.exit(1)
    
    print("Checking/installing black...")
    if not ensure_package_installed("black", "black"):
        print("ERROR: Failed to install black")
        sys.exit(1)
    
    # Verify installations
    try:
        ruff_path = subprocess.check_output([sys.executable, "-m", "pip", "show", "ruff"], 
                                          text=True).split('\n')[0]
        print(f"Ruff found: {ruff_path}")
    except subprocess.CalledProcessError:
        print("ERROR: ruff not found in environment")
        sys.exit(1)
    
    try:
        black_path = subprocess.check_output([sys.executable, "-m", "pip", "show", "black"], 
                                           text=True).split('\n')[0]
        print(f"Black found: {black_path}")
    except subprocess.CalledProcessError:
        print("ERROR: black not found in environment")
        sys.exit(1)
    
    # Create configuration files
    create_ruff_config()
    create_pyproject_config()
    
    # Run checks to verify configuration
    print("\nRunning ruff check...")
    try:
        result = subprocess.run([sys.executable, "-m", "ruff", "check", "."], 
                              cwd=Path(__file__).parent.parent,
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print("✓ ruff check passed (no issues found)")
        else:
            print("ruff check found issues (expected if code is not yet formatted):")
            print(result.stdout)
            print(result.stderr)
    except Exception as e:
        print(f"Error running ruff check: {e}")
    
    print("\nRunning black check...")
    try:
        result = subprocess.run([sys.executable, "-m", "black", "--check", "."], 
                              cwd=Path(__file__).parent.parent,
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print("✓ black check passed (all files formatted correctly)")
        else:
            print("black check found files that need formatting (expected if code is not yet formatted):")
            print(result.stdout)
            print(result.stderr)
    except Exception as e:
        print(f"Error running black check: {e}")
    
    print("\nLinting and formatting configuration complete.")

if __name__ == "__main__":
    main()