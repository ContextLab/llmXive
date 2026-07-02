import subprocess
import sys
from pathlib import Path
from setup_requirements import check_package, install_dependencies

def setup_linting_tools():
    """
    Installs and configures flake8 and black for the project.
    This function ensures the tools are available and creates the configuration files.
    """
    project_root = Path(__file__).parent.parent
    requirements_file = project_root / "code" / "requirements.txt"
    
    # Ensure dependencies are installed
    if not check_package("flake8"):
        print("Installing flake8...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flake8"])
    
    if not check_package("black"):
        print("Installing black...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "black"])
        
    if not check_package("isort"):
        print("Installing isort...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "isort"])

    # Create .flake8 configuration
    flake8_config = project_root / ".flake8"
    if not flake8_config.exists():
        with open(flake8_config, "w") as f:
            f.write("""[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info,
    .venv,
    venv,
    env
per-file-ignores =
    __init__.py:F401
""")
        print(f"Created {flake8_config}")
    else:
        print(f"{flake8_config} already exists.")

    # Create pyproject.toml for Black and Isort
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        with open(pyproject, "w") as f:
            f.write("""[tool.black]
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

[tool.isort]
profile = "black"
line_length = 88
skip_gitignore = true
""")
        print(f"Created {pyproject}")
    else:
        print(f"{pyproject} already exists.")

    print("Linting and formatting tools configured successfully.")

if __name__ == "__main__":
    setup_linting_tools()