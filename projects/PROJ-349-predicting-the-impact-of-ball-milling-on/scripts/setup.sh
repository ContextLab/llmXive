#!/bin/bash
# Setup script for PROJ-349-predicting-the-impact-of-ball-milling-on
# Creates the directory structure defined in scripts/setup_manifest.txt

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Setting up project structure in: $PROJECT_ROOT"

# Read directories from manifest and create them
while IFS= read -r line; do
    # Skip comments and empty lines
    [[ "$line" =~ ^#.*$ ]] && continue
    [[ -z "$line" ]] && continue
    
    # Trim whitespace
    dir=$(echo "$line" | xargs)
    
    if [[ -n "$dir" ]]; then
        full_path="$PROJECT_ROOT/$dir"
        if [[ ! -d "$full_path" ]]; then
            mkdir -p "$full_path"
            echo "Created: $dir"
        else
            echo "Exists: $dir"
        fi
    fi
done < "$SCRIPT_DIR/setup_manifest.txt"

# Create .gitignore if it doesn't exist
GITIGNORE="$PROJECT_ROOT/.gitignore"
if [[ ! -f "$GITIGNORE" ]]; then
    cat > "$GITIGNORE" << 'EOF'
    # Python
    __pycache__/
    *.py[cod]
    *$py.class
    .venv/
    venv/
    ENV/
    env/

    # Jupyter
    .ipynb_checkpoints/

    # IDE
    .idea/
    .vscode/
    *.swp
    *.swo

    # Data
    data/raw/*.csv
    data/raw/*.json
    data/processed/*.parquet
    data/processed/*.json
    data/splits/

    # Results
    results/

    # Environment
    .env
    *.log

    # OS
    .DS_Store
    Thumbs.db
    EOF
    echo "Created: .gitignore"
fi

echo ""
echo "Project structure setup complete!"
echo "Next steps:"
echo "  1. Review the created directories"
echo "  2. Run 'pip install -r requirements.txt' (after creating requirements.txt)"
echo "  3. Initialize git: git init"
echo "  4. Configure linting: black, flake8"
