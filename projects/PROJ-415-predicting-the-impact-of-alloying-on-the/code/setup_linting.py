"""
Linting and Formatting Configuration Setup for llmXive Project.

This script initializes the project with ruff (linting) and black (formatting)
configurations, ensuring code quality standards are met.
"""
import os
import sys
from pathlib import Path
import tomli_w
import tomli

def create_ruff_config(project_root: Path) -> None:
    """Create or update pyproject.toml with ruff configuration."""
    config_path = project_root / "pyproject.toml"
    
    # Default ruff configuration
    ruff_config = {
        "project": {
            "name": "llmXive-alloy-diffusion",
            "version": "0.1.0",
            "description": "Predicting the impact of alloying on diffusion activation energy",
            "requires-python": ">=3.11",
            "dependencies": [
                "pandas>=2.0.0",
                "numpy>=1.24.0",
                "scikit-learn>=1.3.0",
                "scipy>=1.11.0",
                "requests>=2.31.0",
                "pymatgen>=2023.0.0",
                "pytest>=7.4.0",
                "ruff>=0.1.0",
                "black>=23.0.0",
                "tomli>=2.0.0",
                "tomli-w>=1.0.0"
            ]
        },
        "tool": {
            "ruff": {
                "target-version": "py311",
                "line-length": 88,
                "select": [
                    "E",  # pycodestyle errors
                    "W",  # pycodestyle warnings
                    "F",  # Pyflakes
                    "I",  # isort
                    "B",  # flake8-bugbear
                    "C4", # flake8-comprehensions
                    "UP"  # pyupgrade
                ],
                "ignore": [
                    "E501",  # Line too long (black handles this)
                    "B008",  # Do not perform function calls in argument defaults
                    "C408"   # Unnecessary dict call
                ],
                "exclude": [
                    ".git",
                    "__pycache__",
                    "build",
                    "dist",
                    ".venv",
                    "data/raw",
                    "data/curated",
                    "models",
                    "reports"
                ],
                "per-file-ignores": {
                    "__init__.py": ["F401", "F403"],
                    "tests/*": ["S101", "B018"]  # Allow assert and unused expressions in tests
                }
            },
            "black": {
                "target-version": ["py311"],
                "line-length": 88,
                "exclude": r"/(\.git|__pycache__|build|dist|\.venv|data|models|reports)/"
            },
            "isort": {
                "profile": "black",
                "line_length": 88
            }
        }
    }

    if config_path.exists():
        # Read existing config and merge
        try:
            with open(config_path, "rb") as f:
                existing_config = tomli.load(f)
            
            # Merge tool sections
            if "tool" in existing_config:
                for tool_name, tool_config in ruff_config.get("tool", {}).items():
                    if tool_name not in existing_config["tool"]:
                        existing_config["tool"][tool_name] = tool_config
                    else:
                        # Deep merge for nested configs
                        for key, value in tool_config.items():
                            existing_config["tool"][tool_name][key] = value
            
            # Merge project dependencies if needed
            if "project" in ruff_config:
                if "project" not in existing_config:
                    existing_config["project"] = ruff_config["project"]
                elif "dependencies" in ruff_config["project"]:
                    existing_deps = set(existing_config["project"].get("dependencies", []))
                    new_deps = ruff_config["project"]["dependencies"]
                    for dep in new_deps:
                        if dep not in existing_deps:
                            existing_config["project"].setdefault("dependencies", []).append(dep)
            
            ruff_config = existing_config
        except Exception as e:
            print(f"Warning: Could not merge existing pyproject.toml: {e}. Creating new file.")

    # Write the configuration
    with open(config_path, "wb") as f:
        tomli_w.dump(ruff_config, f)
    
    print(f"✓ Created/updated {config_path} with ruff and black configuration")

def create_ruff_toml(project_root: Path) -> None:
    """Create standalone ruff.toml for immediate use."""
    ruff_toml_path = project_root / "ruff.toml"
    
    content = """# Ruff configuration for llmXive project
target-version = "py311"
line-length = 88

select = [
    "E",
    "W",
    "F",
    "I",
    "B",
    "C4",
    "UP"
]

ignore = [
    "E501",
    "B008",
    "C408"
]

exclude = [
    ".git",
    "__pycache__",
    "build",
    "dist",
    ".venv",
    "data/raw",
    "data/curated",
    "models",
    "reports"
]

[per-file-ignores]
"__init__.py" = ["F401", "F403"]
"tests/*" = ["S101", "B018"]
"""
    
    with open(ruff_toml_path, "w") as f:
        f.write(content)
    
    print(f"✓ Created {ruff_toml_path}")

def create_pre_commit_config(project_root: Path) -> None:
    """Create .pre-commit-config.yaml for automated linting."""
    pre_commit_path = project_root / ".pre-commit-config.yaml"
    
    content = """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
- id: ruff
  args: [--fix]
- id: ruff-format
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
- id: black
  language_version: python3.11
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
- id: isort
  args: ["--profile", "black"]
"""
    
    with open(pre_commit_path, "w") as f:
        f.write(content)
    
    print(f"✓ Created {pre_commit_path}")

def create_gitignore_update(project_root: Path) -> None:
    """Ensure .gitignore includes linting artifacts."""
    gitignore_path = project_root / ".gitignore"
    
    linting_entries = """
# Linting and Formatting
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Ruff
.ruff_cache/

# Black
.black_cache/

# IDE
.idea/
.vscode/
*.swp
*.swo
"""
    
    if gitignore_path.exists():
        with open(gitignore_path, "r") as f:
            content = f.read()
        if ".ruff_cache/" not in content:
            with open(gitignore_path, "a") as f:
                f.write("\n# Linting artifacts\n.ruff_cache/\n")
            print("✓ Updated .gitignore with ruff cache")
    else:
        with open(gitignore_path, "w") as f:
            f.write(linting_entries)
        print("✓ Created .gitignore with linting entries")

def main():
    """Main entry point for linting setup."""
    project_root = Path(__file__).resolve().parent.parent
    
    print("Setting up linting and formatting tools...")
    print(f"Project root: {project_root}")
    
    try:
        create_ruff_config(project_root)
        create_ruff_toml(project_root)
        create_pre_commit_config(project_root)
        create_gitignore_update(project_root)
        
        print("\n✓ Linting and formatting setup complete!")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run formatter: black code/ tests/")
        print("  3. Run linter: ruff check code/ tests/")
        print("  4. (Optional) Install pre-commit hooks: pre-commit install")
        
    except Exception as e:
        print(f"✗ Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()