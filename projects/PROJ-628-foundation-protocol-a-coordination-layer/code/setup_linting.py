"""
Script to initialize linting (ruff) and formatting (black) configuration
and install pre-commit hooks for the Foundation Protocol project.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], cwd: Path | None = None) -> bool:
    """Run a shell command and return True if successful."""
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Exit code: {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        return False

def install_precommit_hooks(cwd: Path) -> bool:
    """Install pre-commit hooks."""
    print("Installing pre-commit hooks...")
    # Ensure pre-commit is installed
    if not run_command([sys.executable, "-m", "pip", "install", "pre-commit"], cwd=cwd):
        print("Failed to install pre-commit. Please install it manually: pip install pre-commit")
        return False
    
    # Initialize hooks
    if not run_command(["pre-commit", "install"], cwd=cwd):
        print("Failed to install pre-commit hooks. Please run 'pre-commit install' manually.")
        return False
    
    return True

def main():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    
    print(f"Setting up linting and formatting for project at: {project_root}")
    print(f"Code directory: {code_dir}")
    
    # Verify .pre-commit-config.yaml exists
    config_file = code_dir / ".pre-commit-config.yaml"
    if not config_file.exists():
        print(f"Error: {config_file} not found. Please ensure the configuration file exists.")
        sys.exit(1)
    
    # Verify .gitignore exists (create if missing)
    gitignore_file = code_dir / ".gitignore"
    if not gitignore_file.exists():
        print("Creating .gitignore...")
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
        .installed.cfg
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
        .cache
        nosetests.xml
        coverage.xml
        *.cover
        .hypothesis/
        .pytest_cache/

        # Translations
        *.mo
        *.pot

        # Environments
        .env
        .venv
        env/
        venv/
        ENV/
        env.bak/
        venv.bak/

        # IDE
        .idea/
        .vscode/
        *.swp
        *.swo
        *~

        # Jupyter Notebook
        .ipynb_checkpoints

        # pyenv
        .python-version

        # mypy
        .mypy_cache/
        .dmypy.json
        dmypy.json

        # Pyre type checker
        .pyre/

        # OS
        .DS_Store
        Thumbs.db

        # Project specific
        results/
        data/generated/
        state/
        logs/
        """.strip()
        gitignore_file.write_text(gitignore_content)
        print(".gitignore created.")
    
    # Check if git is initialized
    git_dir = project_root / ".git"
    if not git_dir.exists():
        print("Warning: Git repository not initialized. Initializing...")
        if not run_command(["git", "init"], cwd=project_root):
            print("Failed to initialize git repository.")
            sys.exit(1)
    
    # Install pre-commit hooks
    if not install_precommit_hooks(project_root):
        print("Setup completed with warnings. Please install pre-commit hooks manually.")
        sys.exit(0)
    
    # Run pre-commit on all files (optional, for initial check)
    print("\nRunning pre-commit on all files (this may take a moment)...")
    run_command(["pre-commit", "run", "--all-files"], cwd=project_root)
    
    print("\nLinting and formatting setup complete!")
    print("Run 'pre-commit run' to manually trigger checks on staged files.")
    print("Run 'pre-commit run --all-files' to check all files.")

if __name__ == "__main__":
    main()
