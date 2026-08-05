"""
Setup script to configure linting (ruff) and formatting (black) tools.
This script installs the tools (if not present) and generates configuration files.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and print status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(f"✓ {description} completed successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with error: {e}\n")
        return False

def check_config_files(project_root):
    """Verify that configuration files exist."""
    config_files = [
        project_root / "pyproject.toml",
        project_root / ".ruff.toml",
    ]
    missing = [f for f in config_files if not f.exists()]
    if missing:
        print(f"Warning: Missing configuration files: {missing}")
        return False
    print("✓ All configuration files present.")
    return True

def create_ruff_config(project_root):
    """Create .ruff.toml configuration file."""
    config_path = project_root / ".ruff.toml"
    if config_path.exists():
        print(f"File {config_path} already exists. Skipping creation.")
        return True

    content = """
# Ruff configuration for llmXive project

target-version = "py311"
line-length = 88

[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line-too-long (handled by black)
    "B008", # do-not-perform-function-calls-in-argument-defaults (often needed for config)
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[lint.isort]
known-first-party = ["utils", "01_ingest", "02_process", "03_model", "04_validate", "05_viz"]
"""
    with open(config_path, "w") as f:
        f.write(content)
    print(f"Created {config_path}")
    return True

def create_black_config(project_root):
    """Ensure Black configuration exists in pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    
    if pyproject_path.exists():
        with open(pyproject_path, "r") as f:
            content = f.read()
        if "[tool.black]" in content:
            print(f"Black config already present in {pyproject_path}")
            return True
    else:
        content = ""

    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = 'code/.*\\.pyi?$'
"""
    if pyproject_path.exists():
        with open(pyproject_path, "a") as f:
            f.write(black_section)
    else:
        with open(pyproject_path, "w") as f:
            f.write(black_section)
    print(f"Updated {pyproject_path} with Black configuration.")
    return True

def main():
    """Main entry point for linting setup."""
    project_root = Path(__file__).resolve().parent.parent
    print(f"Setting up linting and formatting tools for project at: {project_root}")

    # 1. Ensure tools are installed
    print("\n--- Step 1: Installing Tools ---")
    install_success = True
    if not run_command([sys.executable, "-m", "pip", "install", "-q", "ruff"], "Install ruff"):
        install_success = False
    if not run_command([sys.executable, "-m", "pip", "install", "-q", "black"], "Install black"):
        install_success = False

    if not install_success:
        print("Failed to install tools. Please install manually: pip install ruff black")
        sys.exit(1)

    # 2. Create configuration files
    print("\n--- Step 2: Creating Configuration Files ---")
    create_ruff_config(project_root)
    create_black_config(project_root)

    # 3. Verify configurations
    print("\n--- Step 3: Verifying Configurations ---")
    check_config_files(project_root)

    # 4. Run initial format check (dry run)
    print("\n--- Step 4: Running Initial Format Check (Check Only) ---")
    # We run black --check on the code directory to see if it passes
    code_dir = project_root / "code"
    if code_dir.exists():
        if not run_command(
            [sys.executable, "-m", "black", "--check", "--diff", str(code_dir)],
            "Black check (no auto-fix)"
        ):
            print("Note: Code formatting issues detected. Run 'black code/' to fix.")
    else:
        print("Warning: 'code/' directory not found, skipping format check.")

    # 5. Run initial lint check
    print("\n--- Step 5: Running Initial Lint Check ---")
    if code_dir.exists():
        if not run_command(
            [sys.executable, "-m", "ruff", "check", str(code_dir)],
            "Ruff check"
        ):
            print("Note: Linting issues detected. Run 'ruff check --fix code/' to attempt fixes.")
    else:
        print("Warning: 'code/' directory not found, skipping lint check.")

    print("\n--- Setup Complete ---")
    print("Linting (ruff) and Formatting (black) are configured.")
    print("To format code:   black code/")
    print("To lint code:     ruff check code/")
    print("To fix lint issues: ruff check --fix code/")

if __name__ == "__main__":
    main()