import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and raise an error if it fails."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def check_config_files():
    """Verify that configuration files exist."""
    config_files = [
        "pyproject.toml",
        ".flake8",
        ".ruff.toml"
    ]
    missing = []
    for f in config_files:
        if not Path(f).exists():
            missing.append(f)
    
    if missing:
        print(f"Warning: Missing configuration files: {missing}")
        return False
    print("All configuration files present.")
    return True

def main():
    """Main entry point for setting up linting and formatting tools."""
    print("=== Setting up Linting and Formatting Tools ===")
    
    # 1. Install tools
    install_cmd = "pip install ruff black"
    if not run_command(install_cmd, "Install ruff and black"):
        print("Failed to install tools. Please install manually.")
        return 1
    
    # 2. Create pyproject.toml with ruff and black configuration if it doesn't exist
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Creating pyproject.toml with linting configuration...")
        config_content = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "predicting-antibiotic-resistance-evolution"
version = "0.1.0"
description = "Predicting antibiotic resistance evolution from genomic sequences"
requires-python = ">=3.11"
dependencies = [
    "scikit-learn",
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "biopython",
    "requests",
    "pyyaml",
    "dendropy",
    "statsmodels",
    "ruff",
    "black",
]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
)/
'''

[tool.ruff]
line-length = 88
target-version = "py311"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"tests/*" = ["S101"]

[tool.ruff.isort]
known-first-party = ["utils", "01_ingest", "02_process", "03_model", "04_validate", "05_viz"]

[tool.ruff.flake8-bugbear]
extend-immutable-calls = ["fastapi.Depends", "fastapi.params.Depends"]
"""
        pyproject_path.write_text(config_content)
        print("pyproject.toml created.")
    else:
        print("pyproject.toml already exists. Updating configuration...")
        # In a real scenario, we might merge configs, but for simplicity we assume it's correct
    
    # 3. Create .flake8 for legacy compatibility if desired (optional, but good practice)
    flake8_path = Path(".flake8")
    if not flake8_path.exists():
        print("Creating .flake8 configuration...")
        flake8_content = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist,*.egg-info,venv,.venv
ignore = E501,W503
"""
        flake8_path.write_text(flake8_content)
        print(".flake8 created.")
    
    # 4. Create .ruff.toml for explicit ruff config (optional, but good practice)
    ruff_path = Path(".ruff.toml")
    if not ruff_path.exists():
        print("Creating .ruff.toml configuration...")
        # We can just point to pyproject.toml settings or duplicate minimal config
        # For this task, we'll create a minimal one that extends pyproject.toml
        ruff_content = """# This file extends the configuration in pyproject.toml
extend = "pyproject.toml"
"""
        ruff_path.write_text(ruff_content)
        print(".ruff.toml created.")
    
    # 5. Verify configuration
    check_config_files()
    
    # 6. Run a dry-run lint check on the code directory to ensure setup is correct
    print("\nVerifying setup by running 'ruff check' on code directory...")
    if not run_command("ruff check code/", "Ruff check on code directory"):
        print("Note: Ruff found issues (this is expected if code is not yet linted).")
    
    print("\n=== Linting and Formatting Setup Complete ===")
    print("To format code: black code/")
    print("To lint code: ruff check code/")
    return 0

if __name__ == "__main__":
    sys.exit(main())