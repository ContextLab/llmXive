import subprocess
import sys
from pathlib import Path

def install_tools():
    """Install ruff and black into the current environment."""
    print("Installing linting and formatting tools (ruff, black)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
        print("Tools installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install tools: {e}")
        sys.exit(1)

def create_ruff_config(project_root: Path):
    """Create a .ruff.toml configuration file."""
    config_path = project_root / ".ruff.toml"
    content = """# Ruff configuration for llmXive project
target-version = "py310"

[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (black handles this)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[lint.per-file-ignores]
"tests/*" = ["S101"]  # assert allowed in tests

[lint.isort]
known-first-party = ["src"]
"""
    config_path.write_text(content)
    print(f"Created ruff config: {config_path}")

def create_black_config(project_root: Path):
    """Create a pyproject.toml section for Black if not exists, or standalone config."""
    # We will add to pyproject.toml if it exists, otherwise create a minimal one
    pyproject_path = project_root / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py310']
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
target-version = "py310"
"""

    if pyproject_path.exists():
        # Append to existing file
        with open(pyproject_path, "a") as f:
            f.write("\n" + black_section)
        print(f"Updated pyproject.toml with Black config: {pyproject_path}")
    else:
        pyproject_path.write_text(f"[project]\nname = \"llmxive\"\nversion = \"0.1.0\"\n" + black_section)
        print(f"Created pyproject.toml with Black config: {pyproject_path}")

def create_git_hooks(project_root: Path):
    """Create a simple pre-commit hook to run linters."""
    hooks_dir = project_root / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    hook_path = hooks_dir / "pre-commit"
    hook_content = """#!/bin/bash
# Pre-commit hook for linting and formatting

# Run black to format code
echo "Running Black..."
black --check code/ tests/ src/ || (echo "Please run 'black code/ tests/ src/' to fix formatting"; exit 1)

# Run ruff to lint code
echo "Running Ruff..."
ruff check code/ tests/ src/ || (echo "Please fix linting errors"; exit 1)

echo "Linting passed!"
exit 0
"""
    hook_path.write_text(hook_content)
    # Make executable (on Unix-like systems)
    try:
        hook_path.chmod(0o755)
    except PermissionError:
        pass
    print(f"Created pre-commit hook: {hook_path}")

def main():
    project_root = Path.cwd()
    print(f"Setting up linting and formatting for project at: {project_root}")
    
    install_tools()
    create_ruff_config(project_root)
    create_black_config(project_root)
    create_git_hooks(project_root)
    
    print("\nSetup complete! Run 'black code/ tests/ src/' and 'ruff check code/ tests/ src/' to verify.")

if __name__ == "__main__":
    main()