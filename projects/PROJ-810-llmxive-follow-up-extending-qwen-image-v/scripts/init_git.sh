#!/bin/bash
# Script to initialize git repository if not already initialized
# and ensure .gitignore is present.

set -e

PROJECT_ROOT="projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v"

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "Error: Project directory $PROJECT_ROOT does not exist."
    exit 1
fi

cd "$PROJECT_ROOT"

if [ -d ".git" ]; then
    echo "Git repository already initialized in $PROJECT_ROOT"
    # Ensure .gitignore exists
    if [ ! -f ".gitignore" ]; then
        echo "Warning: .gitignore missing. Creating default."
        # In a real scenario, this might copy from a template or create one
        touch .gitignore
    fi
else
    echo "Initializing git repository in $PROJECT_ROOT"
    git init
    
    # Ensure .gitignore exists
    if [ ! -f ".gitignore" ]; then
        echo "Creating .gitignore..."
        cat > .gitignore << 'EOF'
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
        cache/
        .nosercache
        .hypothesis/
        .pytest_cache/

        # Transient virtual envs
        .env
        .venv
        env/
        venv/
        ENV/

        # IDEs
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

        # Data artifacts (keep raw data, ignore processed/interim if not needed in repo)
        data/raw/
        data/interim/
        data/processed/
        data/external/

        # Results and logs (generated during execution)
        data/results/
        logs/
        figures/

        # OS files
        .DS_Store
        Thumbs.db

        # Project specific
        .ruff_cache/
        .mypy_cache/
        .pytest_cache/
        .coverage
        coverage.xml
        htmlcov/
        .hypothesis/
        EOF
    fi
    
    echo "Git repository initialized successfully."
fi
