#!/bin/bash
# Setup script for linting (ruff) and formatting (black) tools.
# This script installs the tools and generates configuration files.

set -e

echo "Installing linting and formatting tools..."
pip install ruff black

echo "Generating ruff configuration..."
cat > code/ruff.toml << 'EOF'
[lint]
select = ["E", "F", "W", "I", "N", "B", "C4", "UP"]
ignore = ["E501", "B008"]  # Ignore line length and some common false positives
target-version = "py39"

[format]
line-length = 100
indent-width = 4

[lint.per-file-ignores]
"code/__init__.py" = ["F401"]
"code/utils/__init__.py" = ["F401"]
"tests/*" = ["S101"]  # Allow asserts in tests
EOF

echo "Generating black configuration..."
cat > code/pyproject.toml << 'EOF'
[tool.black]
line-length = 100
target-version = ['py39']
include = '\.pyi?$'
exclude = '''
/(
    \.git
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
)/
'''

[tool.ruff]
# Ruff config is in ruff.toml, this is for compatibility if needed
line-length = 100
target-version = "py39"
EOF

echo "Linting and formatting tools configured successfully."
echo "To run linter: ruff check code/"
echo "To run formatter: black code/"
echo "To run both: ruff check code/ && black code/"
