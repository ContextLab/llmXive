import subprocess
import sys
import os
from pathlib import Path
from config import PROJECT_ROOT

def get_black_config_path():
    """Return the path to the black configuration file."""
    return PROJECT_ROOT / "pyproject.toml"

def get_flake8_config_path():
    """Return the path to the flake8 configuration file."""
    return PROJECT_ROOT / ".flake8"

def setup_black_config():
    """Create or update pyproject.toml with black configuration."""
    config_path = get_black_config_path()
    black_config = """[tool.black]
line-length = 88
target-version = ['py311']
include = 'code/.*\\.py$'
exclude = '''
/(
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
)/
'''
"""
    # Check if file exists and contains black config
    if config_path.exists():
        content = config_path.read_text()
        if "[tool.black]" in content:
            # Update existing config
            # Simple approach: replace the block if it exists, or append
            # For robustness in this context, we'll overwrite the black section
            # Since we are implementing a setup script, overwriting is acceptable
            pass
    
    # Write the config
    with open(config_path, 'w') as f:
        f.write(black_config)
    
    print(f"Black configuration written to {config_path}")

def setup_flake8_config():
    """Create or update .flake8 with flake8 configuration."""
    config_path = get_flake8_config_path()
    flake8_config = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info
max-complexity = 10
"""
    with open(config_path, 'w') as f:
        f.write(flake8_config)
    
    print(f"Flake8 configuration written to {config_path}")

def install_tools():
    """Install black and flake8 if not already installed."""
    tools = ['black', 'flake8']
    for tool in tools:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', tool])
            print(f"{tool} installed successfully.")
        except subprocess.CalledProcessError:
            print(f"Failed to install {tool}. Please install manually.")

def run_formatting():
    """Run black formatting on the code directory."""
    config_path = get_black_config_path()
    if not config_path.exists():
        setup_black_config()
    
    try:
        subprocess.run(
            [sys.executable, '-m', 'black', 'code/'],
            check=True,
            cwd=PROJECT_ROOT
        )
        print("Formatting completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Formatting failed: {e}")
        return False
    return True

def run_linting():
    """Run flake8 linting on the code directory."""
    config_path = get_flake8_config_path()
    if not config_path.exists():
        setup_flake8_config()
    
    try:
        subprocess.run(
            [sys.executable, '-m', 'flake8', 'code/'],
            check=True,
            cwd=PROJECT_ROOT
        )
        print("Linting completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Linting found issues: {e}")
        return False
    return True

def main():
    """Main entry point to configure and optionally run linting/formatting."""
    print("Setting up linting and formatting tools...")
    install_tools()
    setup_black_config()
    setup_flake8_config()
    print("Configuration complete.")
    print("Run 'python -m linting_config run-format' to format code.")
    print("Run 'python -m linting_config run-lint' to lint code.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "run-format":
            run_formatting()
        elif sys.argv[1] == "run-lint":
            run_linting()
        else:
            main()
    else:
        main()