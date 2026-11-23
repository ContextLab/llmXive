import os
from pathlib import Path

def ensure_init_files():
    """
    Creates __init__.py in every src/ and tests/ directory.
    Also ensures .gitignore is configured correctly.
    """
    project_root = Path(__file__).resolve().parent.parent

    # Directories that need __init__.py
    init_dirs = [
        "src",
        "src/models",
        "src/data",
        "src/training",
        "src/experiments",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration",
    ]

    for dir_path in init_dirs:
        full_path = project_root / dir_path
        init_file = full_path / "__init__.py"
        if full_path.exists():
            # Create empty __init__.py if it doesn't exist
            if not init_file.exists():
                init_file.touch()
                print(f"Created {init_file}")
            else:
                print(f"Skipped existing {init_file}")
        else:
            print(f"Warning: Directory {full_path} does not exist, skipping __init__.py creation.")

    # Create .gitignore
    gitignore_path = project_root / ".gitignore"
    gitignore_content = """# Data directories
data/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Logs
*.log

# IDE/Editor
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# State files are TRACKED (Constitution Principle V)
# Do NOT ignore state/*.yaml
"""
    if not gitignore_path.exists():
        with open(gitignore_path, "w") as f:
            f.write(gitignore_content)
        print(f"Created .gitignore: {gitignore_path}")
    else:
        print(f"Skipped existing .gitignore: {gitignore_path}")

def main():
    print("Ensuring __init__.py files and .gitignore...")
    ensure_init_files()
    print("Init files and .gitignore setup complete.")

if __name__ == "__main__":
    main()