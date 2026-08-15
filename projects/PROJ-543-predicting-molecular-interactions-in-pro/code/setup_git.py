"""
Setup script to initialize a Git repository and configure .gitignore.
This script ensures the project version control is ready for collaboration.
"""
import os
import subprocess
import sys
from pathlib import Path

def initialize_git_repo(root_dir: Path) -> bool:
    """Initialize a git repository if one does not exist."""
    git_dir = root_dir / ".git"
    if git_dir.exists():
        print(f"Git repository already exists at {root_dir}")
        return True

    try:
        subprocess.run(
            ["git", "init"],
            cwd=root_dir,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Initialized empty Git repository in {root_dir}/.git/")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to initialize git repository: {e.stderr}", file=sys.stderr)
        return False

def configure_git_ignore(root_dir: Path) -> bool:
    """Ensure .gitignore exists with standard Python/Data patterns."""
    gitignore_path = root_dir / ".gitignore"
    
    standard_patterns = [
        "# Byte-compiled / optimized / DLL files",
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.so",
        "",
        "# C extensions",
        "*.so",
        "*.pyd",
        "",
        "# Distribution / packaging",
        ".Python",
        "build/",
        "develop-eggs/",
        "dist/",
        "downloads/",
        "eggs/",
        ".eggs/",
        "lib/",
        "lib64/",
        "parts/",
        "sdist/",
        "var/",
        "wheels/",
        "*.egg-info/",
        "installed-files.txt",
        "*.egg",
        "",
        "# Virtual Environments",
        ".venv/",
        "venv/",
        "ENV/",
        "env/",
        "code/venv/",
        "code/.venv/",
        "",
        "# IDE",
        ".idea/",
        ".vscode/",
        "*.swp",
        "*.swo",
        "*~",
        ".project",
        ".pydevproject",
        "",
        "# Jupyter Notebook",
        ".ipynb_checkpoints",
        "",
        "# pyenv",
        ".python-version",
        "",
        "# mypy",
        ".mypy_cache/",
        ".dmypy.json",
        "dmypy.json",
        "",
        "# Pyre type checker",
        ".pyre/",
        "",
        "# Data artifacts (Large files, binary blobs)",
        "data/raw/**/*.tar.gz",
        "data/raw/**/*.zip",
        "data/raw/**/*.pdb",
        "data/raw/**/*.gz",
        "data/processed/*.pt",
        "data/processed/*.pkl",
        "data/processed/*.h5",
        "data/processed/*.hdf5",
        "data/results/*.json",
        "data/results/*.csv",
        "data/results/*.png",
        "data/results/*.pdf",
        "data/reference/*.json",
        "data/reference/*.csv",
        "",
        "# Logs",
        "*.log",
        "logs/",
        "",
        "# OS generated files",
        ".DS_Store",
        ".DS_Store?",
        "._*",
        ".Spotlight-V100",
        ".Trashes",
        "ehthumbs.db",
        "Thumbs.db",
        "",
        "# Test coverage",
        ".coverage",
        "htmlcov/",
        ".pytest_cache/",
        ".tox/",
        "",
        "# Secrets",
        ".env",
        ".secret*",
        "secrets/",
        "*.key",
        "*.pem",
    ]

    content = "\n".join(standard_patterns) + "\n"

    if gitignore_path.exists():
        print(f"Updating existing .gitignore at {gitignore_path}")
        # Append missing patterns or overwrite if structure changed significantly
        # For simplicity in this setup task, we overwrite to ensure correctness
        with open(gitignore_path, "w") as f:
            f.write(content)
        print("Updated .gitignore")
    else:
        print(f"Creating .gitignore at {gitignore_path}")
        with open(gitignore_path, "w") as f:
            f.write(content)
        print("Created .gitignore")
    
    return True

def main():
    root_dir = Path(__file__).resolve().parent.parent
    print(f"Running Git setup for project at: {root_dir}")

    if not initialize_git_repo(root_dir):
        sys.exit(1)
    
    if not configure_git_ignore(root_dir):
        sys.exit(1)

    print("Git initialization and .gitignore configuration complete.")

if __name__ == "__main__":
    main()