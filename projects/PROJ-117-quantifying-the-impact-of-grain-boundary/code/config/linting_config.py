"""
Configuration constants for Ruff and Black linting/formatting tools.
Provides command strings and configuration file contents.
"""

def get_ruff_command() -> str:
    """Return the command to run Ruff check."""
    return "ruff check ."

def get_ruff_fix_command() -> str:
    """Return the command to run Ruff check with auto-fix."""
    return "ruff check . --fix"

def get_black_command() -> str:
    """Return the command to run Black formatting."""
    return "black ."

def get_black_check_command() -> str:
    """Return the command to run Black in check-only mode."""
    return "black --check ."

def get_ruff_config_file_content() -> str:
    """Return the content for .ruff.toml configuration file."""
    return """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501", # line-too-long (handled by black)
    "B008", # do-not-perform-argument-default-lookup-in-function-definition
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""

def get_black_config_file_content() -> str:
    """Return the content for .black.toml configuration file."""
    return """[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
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
"""