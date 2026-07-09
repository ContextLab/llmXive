import os
import subprocess
import sys
from pathlib import Path

def ensure_config_dir():
    """Ensure the project root exists."""
    project_root = Path(__file__).resolve().parent.parent
    project_root.mkdir(parents=True, exist_ok=True)
    return project_root

def create_flake8_config(project_root):
    """Create a .flake8 configuration file."""
    config_path = project_root / ".flake8"
    content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .eggs
"""
    config_path.write_text(content)
    return config_path

def create_black_config(project_root):
    """Create a pyproject.toml section for Black if not exists, or append."""
    config_path = project_root / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
exclude = '''
(
  /(
\.eggs
    | \.git
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
  )/
)
'''
"""
    if not config_path.exists():
        config_path.write_text(black_section)
    else:
        # Check if [tool.black] already exists to avoid duplicates
        content = config_path.read_text()
        if "[tool.black]" not in content:
            config_path.write_text(content + black_section)
    
    return config_path

def create_isort_config(project_root):
    """Create a pyproject.toml section for isort."""
    config_path = project_root / "pyproject.toml"
    
    isort_section = """
[tool.isort]
profile = "black"
line_length = 88
"""
    if not config_path.exists():
        config_path.write_text(isort_section)
    else:
        content = config_path.read_text()
        if "[tool.isort]" not in content:
            config_path.write_text(content + isort_section)
    
    return config_path

def run_formatting(project_root):
    """Run Black and isort on the code directory."""
    code_dir = project_root / "code"
    if not code_dir.exists():
        print("No 'code' directory found to format.")
        return

    print("Running isort...")
    try:
        subprocess.run([sys.executable, "-m", "isort", str(code_dir)], check=True)
        print("isort completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"isort failed: {e}")
        # Non-fatal for setup, but log it

    print("Running Black...")
    try:
        subprocess.run([sys.executable, "-m", "black", str(code_dir)], check=True)
        print("Black completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Black failed: {e}")
        # Non-fatal for setup

def run_linting(project_root):
    """Run Flake8 on the code directory."""
    code_dir = project_root / "code"
    if not code_dir.exists():
        print("No 'code' directory found to lint.")
        return

    print("Running Flake8...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(code_dir)],
            check=False,
            capture_output=False
        )
        if result.returncode == 0:
            print("Flake8 found no issues.")
        else:
            print("Flake8 found issues (see above).")
    except FileNotFoundError:
        print("Flake8 not found. Please install it: pip install flake8")

def main():
    """Main entry point to configure linting tools."""
    print("Configuring linting and formatting tools...")
    project_root = ensure_config_dir()
    
    create_flake8_config(project_root)
    create_black_config(project_root)
    create_isort_config(project_root)
    
    print("Configuration files created.")
    print("Attempting to format and lint existing code (if tools are installed)...")
    
    # Try to install tools if missing, just in case
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "black", "flake8", "isort"], check=True)
    except subprocess.CalledProcessError:
        print("Warning: Could not install linting tools automatically. Please install manually.")

    run_formatting(project_root)
    run_linting(project_root)
    
    print("Linting tool configuration complete.")

if __name__ == "__main__":
    main()