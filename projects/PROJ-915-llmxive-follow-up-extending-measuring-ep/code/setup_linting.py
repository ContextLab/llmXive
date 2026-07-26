import os
from pathlib import Path

def ensure_project_root() -> Path:
    """Ensure we are running from the project root."""
    project_root = Path.cwd()
    if not (project_root / "requirements.txt").exists():
        raise FileNotFoundError(
            f"Project root not found at {project_root}. "
            "Please run this script from the project root directory."
        )
    return project_root

def write_pyproject_toml(project_root: Path) -> None:
    """Create or update pyproject.toml with Black formatting settings."""
    pyproject_path = project_root / "pyproject.toml"
    
    black_config = """[tool.black]
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
"""
    
    # Read existing content if file exists
    existing_content = ""
    if pyproject_path.exists():
        existing_content = pyproject_path.read_text()
    
    # Check if [tool.black] section already exists
    if "[tool.black]" in existing_content:
        # Replace existing section
        lines = existing_content.splitlines()
        new_lines = []
        in_black_section = False
        section_start_idx = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith("[tool.black]"):
                in_black_section = True
                section_start_idx = i
            elif in_black_section and line.strip().startswith("[tool."):
                in_black_section = False
                # Insert black config before this new section
                new_lines.append(black_config.strip())
                new_lines.append("")
                new_lines.append(line)
            elif in_black_section:
                continue
            else:
                new_lines.append(line)
        
        # If black section was at the end
        if in_black_section:
            new_lines.append(black_config.strip())
            new_lines.append("")
        
        pyproject_path.write_text("\n".join(new_lines))
    else:
        # Append new section
        with open(pyproject_path, "a") as f:
            f.write("\n")
            f.write(black_config)

def write_ruff_toml(project_root: Path) -> None:
    """Create .ruff.toml configuration file."""
    ruff_path = project_root / ".ruff.toml"
    
    ruff_config = """# Ruff configuration
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
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[lint.isort]
known-first-party = ["config", "data_models", "features", "ingestion", "validation", "error_handling", "annotation", "secrets_manager", "setup_directories", "validation_gate", "validation_logic"]

[lint.per-file-ignores]
"__init__.py" = ["F401"]
"""
    
    ruff_path.write_text(ruff_config)

def main() -> None:
    """Main entry point for linting configuration setup."""
    try:
        project_root = ensure_project_root()
        print(f"Configuring linting tools for project at: {project_root}")
        
        write_pyproject_toml(project_root)
        print("✓ Updated pyproject.toml with Black configuration")
        
        write_ruff_toml(project_root)
        print("✓ Created .ruff.toml configuration")
        
        print("\nLinting and formatting tools configured successfully!")
        print("\nTo use them:")
        print("  Format code:   black code/")
        print("  Check format:  black --check code/")
        print("  Lint code:     ruff check code/")
        print("  Fix linting:   ruff check code/ --fix")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error during setup: {e}")
        exit(1)

if __name__ == "__main__":
    main()