import os
from pathlib import Path

def create_config_files():
    """
    Ensures ruff.toml and pyproject.toml exist in the code/ directory
    with valid configurations for ruff and black.
    """
    base_dir = Path(__file__).parent
    ruff_config = base_dir / "ruff.toml"
    pyproject_config = base_dir / "pyproject.toml"

    if not ruff_config.exists():
        ruff_content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[lint.per-file-ignores]
"tests/*" = ["S101"] # assert allowed in tests

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
        ruff_config.write_text(ruff_content)
        print(f"Created {ruff_config}")
    else:
        print(f"{ruff_config} already exists.")

    if not pyproject_config.exists():
        pyproject_content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-proj-028"
version = "0.1.0"
description = "Evaluating the effectiveness of different prompting strategies for code generation"
requires-python = ">=3.11"
dependencies = [
    "transformers",
    "torch[cpu]",
    "datasets",
    "scipy",
    "pytest",
    "psutil",
    "ruff",
    "black",
]

[tool.black]
line-length = 88
target-version = ['py311']
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

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.ruff]
target-version = "py311"
line-length = 88
"""
        pyproject_config.write_text(pyproject_content)
        print(f"Created {pyproject_config}")
    else:
        print(f"{pyproject_config} already exists.")

    return True

if __name__ == "__main__":
    create_config_files()