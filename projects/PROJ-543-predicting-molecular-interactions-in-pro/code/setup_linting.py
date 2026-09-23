import subprocess
import sys
import os
from pathlib import Path

def main():
    """
    Configure linting (flake8) and formatting (black) tools for the project.
    
    This script installs flake8 and black into the active virtual environment
    and creates a configuration file for flake8 to enforce project standards.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    # Ensure we are running in the correct context
    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)

    print("Installing linting and formatting tools...")
    
    # Install flake8 and black
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flake8", "black"])
        print("Successfully installed flake8 and black.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)

    # Create .flake8 configuration file in the project root
    flake8_config_path = project_root / ".flake8"
    
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    .venv,
    venv,
    build,
    dist,
    *.egg-info
per-file-ignores =
    # Allow unused imports in __init__.py for exports
    */__init__.py:F401
    # Allow unused arguments in tests
    tests/*:F841
"""
    
    try:
        with open(flake8_config_path, "w") as f:
            f.write(config_content)
        print(f"Created .flake8 configuration at {flake8_config_path}")
    except IOError as e:
        print(f"Failed to create .flake8 configuration: {e}")
        sys.exit(1)

    # Create pyproject.toml for Black configuration if it doesn't exist
    pyproject_path = project_root / "pyproject.toml"
    
    black_config = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | __pycache__
  | build
  | dist
  | \.egg-info
)/
'''
"""

    try:
        if not pyproject_path.exists():
            with open(pyproject_path, "w") as f:
                f.write(black_config)
            print(f"Created pyproject.toml with Black configuration at {pyproject_path}")
        else:
            # Check if [tool.black] section already exists
            with open(pyproject_path, "r") as f:
                content = f.read()
            if "[tool.black]" not in content:
                with open(pyproject_path, "a") as f:
                    f.write("\n" + black_config)
                print(f"Appended Black configuration to existing pyproject.toml")
            else:
                print("Black configuration already exists in pyproject.toml")
    except IOError as e:
        print(f"Failed to configure Black: {e}")
        sys.exit(1)

    print("Linting and formatting tools configured successfully.")
    print("\nTo run linting:")
    print(f"  cd {code_dir} && flake8 .")
    print("\nTo run formatting:")
    print(f"  cd {code_dir} && black .")
    print(f"  cd {code_dir} && black --check .")

if __name__ == "__main__":
    main()