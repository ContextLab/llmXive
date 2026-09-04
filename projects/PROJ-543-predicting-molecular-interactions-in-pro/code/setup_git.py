import os
import subprocess
import sys
from pathlib import Path

def initialize_git_repo(project_root: Path) -> None:
    """Initialize a git repository in the project root if not already initialized."""
    git_dir = project_root / ".git"
    if git_dir.exists():
        print(f"Git repository already initialized at {project_root}")
        return

    try:
        subprocess.run(["git", "init"], cwd=project_root, check=True)
        print(f"Initialized git repository at {project_root}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to initialize git repository: {e}") from e

def configure_git_ignore(project_root: Path) -> None:
    """Create a .gitignore file tailored for Python and data artifacts."""
    gitignore_path = project_root / ".gitignore"
    
    # Define the content for .gitignore
    gitignore_content = """
    # Byte-compiled / optimized / DLL files
    __pycache__/
    *.py[cod]
    *$py.class

    # C extensions
    *.so

    # Distribution / packaging
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
    installed-files.txt
    *.egg

    # PyInstaller
    *.manifest
    *.spec

    # Installer logs
    pip-log.txt
    pip-delete-this-directory.txt

    # Unit test / coverage reports
    htmlcov/
    .coverage
    .coverage.*
    cover/
    .hypothesis/

    # Translations
    *.mo
    *.pot

    # Jupyter Notebook
    .ipynb_checkpoints

    # pyenv
    .python-version

    # Environments
    .env
    .venv
    env/
    venv/
    ENV/
    env.bak/
    venv.bak/

    # IDEs
    .idea/
    .vscode/
    *.swp
    *.swo
    *~

    # OS files
    .DS_Store
    Thumbs.db

    # Project specific: Data artifacts (raw, processed, results)
    # We track code and configs, but not large data files
    data/raw/
    data/processed/
    data/results/
    data/reference/

    # Model weights (large binary files)
    data/processed/*.pt
    data/processed/*.pth
    data/processed/*.h5

    # Logs
    *.log
    logs/

    # Temporary files
    tmp/
    temp/
    *.tmp

    # Hugging Face cache
    .cache/
    hf_cache/

    # Local config overrides
    config.local.yaml
    .env.local
    """

    try:
        gitignore_path.write_text(gitignore_content.strip() + "\n")
        print(f"Created .gitignore at {gitignore_path}")
    except IOError as e:
        raise RuntimeError(f"Failed to create .gitignore: {e}") from e

def main() -> int:
    """Main entry point for git setup."""
    # Determine project root based on the task context
    # The task is in PROJ-543, so we look for the project root relative to the script
    script_dir = Path(__file__).parent.resolve()
    # Assuming the script is in code/ and the project root is the parent of code/
    project_root = script_dir.parent

    print(f"Setting up git repository at: {project_root}")

    try:
        initialize_git_repo(project_root)
        configure_git_ignore(project_root)
        print("Git setup completed successfully.")
        return 0
    except RuntimeError as e:
        print(f"Git setup failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
