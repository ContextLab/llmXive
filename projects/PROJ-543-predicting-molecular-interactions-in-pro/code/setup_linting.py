"""
Linting and formatting configuration setup for the project.

This script configures flake8 and black for the project by creating
the necessary configuration files and installing the tools.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """
    Set up linting (flake8) and formatting (black) tools.
    
    This function:
    1. Installs flake8 and black if not already installed
    2. Creates a .flake8 configuration file at the project root
    3. Creates a pyproject.toml with Black configuration if it doesn't exist
    4. Creates a setup.cfg with additional linting rules if needed
    """
    project_root = Path(__file__).parent.parent
    print(f"Setting up linting and formatting tools in {project_root}")
    
    # Install flake8 and black
    print("Installing flake8 and black...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flake8", "black"])
        print("Successfully installed flake8 and black")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install flake8 or black: {e}")
        sys.exit(1)
    
    # Create .flake8 configuration file
    flake8_config = project_root / ".flake8"
    if not flake8_config.exists():
        print(f"Creating {flake8_config}")
        flake8_config.write_text("""[flake8]
max-line-length = 120
extend-ignore = E203, E266, W503
exclude = .git,__pycache__,build,dist,.venv,venv
per-file-ignores =
    */__init__.py:F401
max-complexity = 10
""")
    else:
        print(f"{flake8_config} already exists, skipping")
    
    # Create or update pyproject.toml with Black configuration
    pyproject_file = project_root / "pyproject.toml"
    black_config_section = """
[tool.black]
line-length = 120
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | build
  | dist
)/
'''
"""
    
    if pyproject_file.exists():
        content = pyproject_file.read_text()
        if "[tool.black]" not in content:
            print(f"Adding Black configuration to {pyproject_file}")
            pyproject_file.write_text(content.rstrip() + black_config_section)
        else:
            print(f"Black configuration already exists in {pyproject_file}")
    else:
        print(f"Creating {pyproject_file} with Black configuration")
        pyproject_file.write_text(f'"""\nProject configuration for PROJ-543\n"""\n{black_config_section}')
    
    # Create setup.cfg with additional linting rules if it doesn't exist
    setup_cfg = project_root / "setup.cfg"
    if not setup_cfg.exists():
        print(f"Creating {setup_cfg}")
        setup_cfg.write_text("""[metadata]
name = proj-543
version = 0.1.0

[options]
packages = find:
python_requires = >=3.11

[flake8]
max-line-length = 120
extend-ignore = E203, E266, W503
exclude = .git,__pycache__,build,dist,.venv,venv
per-file-ignores =
    */__init__.py:F401
max-complexity = 10

[isort]
profile = black
line_length = 120
""")
    else:
        print(f"{setup_cfg} already exists, skipping")
    
    print("Linting and formatting configuration complete!")
    print("\nYou can now run:")
    print("  flake8 code/ tests/")
    print("  black code/ tests/")
    print("  black --check code/ tests/  # Check without modifying files")

if __name__ == "__main__":
    main()