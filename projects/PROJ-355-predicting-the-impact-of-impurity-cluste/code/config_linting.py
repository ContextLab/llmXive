"""
Configuration and setup script for linting (ruff) and formatting (black) tools.
This script creates the necessary configuration files and verifies tool availability.
"""
import os
import subprocess
import sys
from pathlib import Path

def ensure_project_root():
    """Ensure the script is run from the project root."""
    project_root = Path(__file__).resolve().parent.parent
    return project_root

def create_ruff_config(project_root: Path):
    """Create ruff.toml configuration file."""
    config_content = """
    # Ruff configuration for PROJ-355
    line-length = 88
    target-version = "py310"

    [lint]
    select = [
        "E",   # pycodestyle errors
        "W",   # pycodestyle warnings
        "F",   # Pyflakes
        "I",   # isort
        "B",   # flake8-bugbear
        "C4",  # flake8-comprehensions
        "UP",  # pyupgrade
    ]
    ignore = [
        "E501", # Line too long (handled by black)
        "B008", # Do not perform function call in argument defaults (common in data pipelines)
    ]

    [lint.isort]
    known-first-party = ["code", "tests"]

    [format]
    line-length = 88
    """
    config_path = project_root / "ruff.toml"
    config_path.write_text(config_content.strip())
    print(f"Created ruff configuration at: {config_path}")
    return config_path

def create_black_config(project_root: Path):
    """Create pyproject.toml with black configuration if not exists, or update it."""
    pyproject_path = project_root / "pyproject.toml"
    
    black_section = """
    [tool.black]
    line-length = 88
    target-version = ['py310']
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
        content = pyproject_path.read_text()
        if "[tool.black]" not in content:
            pyproject_path.write_text(content + "\n" + black_section.strip())
            print(f"Updated pyproject.toml with black configuration")
        else:
            print(f"Black configuration already exists in pyproject.toml")
    else:
        pyproject_path.write_text(black_section.strip())
        print(f"Created pyproject.toml with black configuration")
    
    return pyproject_path

def verify_tools():
    """Verify that ruff and black are installed."""
    tools = {
        "ruff": "ruff --version",
        "black": "black --version"
    }
    
    missing_tools = []
    
    for tool, cmd in tools.items():
        try:
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✓ {tool} is installed: {result.stdout.strip()}")
            else:
                missing_tools.append(tool)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"\n⚠ Warning: The following tools are missing: {', '.join(missing_tools)}")
        print("Install them using: pip install ruff black")
        return False
    
    return True

def main():
    """Main entry point for configuring linting and formatting tools."""
    project_root = ensure_project_root()
    print(f"Configuring linting and formatting tools for project at: {project_root}")
    
    # Create configuration files
    create_ruff_config(project_root)
    create_black_config(project_root)
    
    # Verify tools are available
    if verify_tools():
        print("\n✅ Configuration complete. Tools are ready to use.")
        print("Run 'ruff check .' to lint and 'black .' to format.")
    else:
        print("\n❌ Configuration incomplete. Please install missing tools.")
        sys.exit(1)

if __name__ == "__main__":
    main()
