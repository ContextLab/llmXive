import os
import subprocess
import sys
from pathlib import Path

# Ensure the code directory exists before writing configs
CODE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = CODE_ROOT.parent

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False

def check_config_files() -> bool:
    """Verify that configuration files exist after creation."""
    ruff_config = PROJECT_ROOT / "ruff.toml"
    black_config = PROJECT_ROOT / "pyproject.toml"
    
    if not ruff_config.exists():
        print("Error: ruff.toml not created")
        return False
    if not black_config.exists():
        print("Error: pyproject.toml (for black) not created")
        return False
    return True

def create_ruff_config() -> bool:
    """Create a ruff.toml configuration file."""
    config_content = """# Ruff configuration for llmXive project
[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line-too-long (handled by black)
    "B008", # do-not-perform-argument-default-lookup-in-function-definition
]

[lint.isort]
known-first-party = ["utils", "01_ingest", "02_process", "03_model", "04_validate", "05_viz"]
section-order = ["future", "standard-library", "third-party", "first-party", "local-folder"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    config_path = PROJECT_ROOT / "ruff.toml"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)
        print(f"Created: {config_path}")
        return True
    except IOError as e:
        print(f"Failed to create ruff config: {e}")
        return False

def create_black_config() -> bool:
    """Create or update pyproject.toml with Black configuration."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
    | \.mypy_cache
    | \.pytest_cache
    | __pycache__
    | build
    | dist
)/
'''
"""
    
    # Check if file exists and has [tool.black]
    needs_update = True
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "[tool.black]" in content:
                print("pyproject.toml already contains [tool.black], skipping update.")
                needs_update = False
            else:
                # Append to existing file
                with open(config_path, "a", encoding="utf-8") as f:
                    f.write(black_section)
                print(f"Appended Black config to: {config_path}")
                return True
    
    if needs_update:
        # Create new file with minimal content + black
        initial_content = """[project]
name = "llmXive-antibiotic-resistance"
version = "0.1.0"
description = "Predicting Antibiotic Resistance Evolution from Genomic Sequences"
requires-python = ">=3.11"
"""
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(initial_content)
                f.write(black_section)
            print(f"Created: {config_path} with Black configuration")
            return True
        except IOError as e:
            print(f"Failed to create pyproject.toml: {e}")
            return False
    
    return True

def main():
    """Main entry point for setting up linting and formatting."""
    print("Setting up linting (Ruff) and formatting (Black)...")
    
    # 1. Create Ruff config
    if not create_ruff_config():
        sys.exit(1)
    
    # 2. Create/Update Black config
    if not create_black_config():
        sys.exit(1)
    
    # 3. Verify files exist
    if not check_config_files():
        sys.exit(1)
    
    # 4. Install tools if not present (optional, but good practice)
    print("\nChecking for ruff and black installation...")
    tools = ["ruff", "black"]
    for tool in tools:
        try:
            subprocess.run([tool, "--version"], check=True, capture_output=True)
            print(f"  ✓ {tool} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"  ✗ {tool} not found. Installing...")
            if not run_command([sys.executable, "-m", "pip", "install", tool], f"Install {tool}"):
                print(f"Warning: Could not install {tool}. Please install manually.")
    
    print("\nLinting and formatting configuration complete.")
    print("Run 'ruff check .' to lint and 'black .' to format.")
    return 0

if __name__ == "__main__":
    sys.exit(main())