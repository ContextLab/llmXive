#!/bin/bash
# Script to install pre-commit hooks for the llmXive project
# This script should be run after cloning the repository
# Usage: ./code/setup_git_hooks.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GIT_DIR="$PROJECT_ROOT/.git"
HOOKS_DIR="$GIT_DIR/hooks"
SAMPLE_HOOKS_DIR="$PROJECT_ROOT/code/.git-hooks"

echo "Setting up Git hooks for llmXive project..."

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook to run pre-commit checks
# This hook ensures seed usage and import validation

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CODE_DIR="$PROJECT_ROOT/code"

# Run pre-commit checks if pre-commit is installed
if command -v pre-commit &> /dev/null; then
    echo "Running pre-commit checks..."
    cd "$PROJECT_ROOT"
    pre-commit run --all-files
else
    # Fallback to manual checks if pre-commit is not installed
    echo "Running manual seed and import checks..."
    
    # Check for seed usage
    if [ -d "$CODE_DIR" ]; then
        python "$CODE_DIR/utils/verify_seed.py" --check-all || exit 1
    fi

    # Check imports
    if [ -d "$CODE_DIR" ]; then
        python "$CODE_DIR/utils/check_imports.py" --check-all || exit 1
    fi
fi

exit 0
EOF

# Make the hook executable
chmod +x "$HOOKS_DIR/pre-commit"

# Install pre-commit package if not already installed
if ! python -m pip show pre-commit &> /dev/null; then
    echo "Installing pre-commit package..."
    python -m pip install pre-commit
fi

# Initialize pre-commit in the repository
cd "$PROJECT_ROOT"
pre-commit install

echo "Git hooks installed successfully!"
echo "Run 'pre-commit install' again if you need to reinstall."
echo "To run checks manually: pre-commit run --all-files"
