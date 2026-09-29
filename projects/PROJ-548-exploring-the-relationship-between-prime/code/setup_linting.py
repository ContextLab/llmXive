"""
Setup script to initialize linting (ruff) and formatting (black) configurations.
This task (T003) ensures the project adheres to consistent code style.
"""
import os
from pathlib import Path

def main():
    """Create configuration files for ruff and black."""
    root = Path(__file__).parent
    code_dir = root / "code"
    
    # Ensure code directory exists
    if not code_dir.exists():
        code_dir.mkdir(parents=True)
        
    # Write ruff.toml
    ruff_config = """[tool.ruff]
line-length = 100
target-version = "py310"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "N",   # pep8-naming
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults (common in data pipelines)
]

[tool.ruff.isort]
known-first-party = ["src", "tests"]
force-sort-within-sections = true

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
"tests/*" = ["S101"]
"""
    ruff_path = code_dir / "ruff.toml"
    ruff_path.write_text(ruff_config)
    print(f"Created {ruff_path}")

    # Write py.toml (Black config)
    black_config = """[tool.black]
line-length = 100
target-version = ['py310']
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
    py_path = code_dir / "py.toml"
    py_path.write_text(black_config)
    print(f"Created {py_path}")

    # Write requirements-dev.txt
    dev_req = """# Development dependencies for linting and formatting
ruff>=0.1.0
black>=23.0.0
pytest>=7.0.0
pytest-cov>=4.0.0
mypy>=1.0.0
"""
    dev_path = code_dir / "requirements-dev.txt"
    dev_path.write_text(dev_req)
    print(f"Created {dev_path}")

    print("Linting and formatting tools configured successfully.")
    print("Run 'pip install -r code/requirements-dev.txt' to install dependencies.")
    print("Run 'ruff check . --fix' to lint and autofix.")
    print("Run 'black .' to format code.")

if __name__ == "__main__":
    main()