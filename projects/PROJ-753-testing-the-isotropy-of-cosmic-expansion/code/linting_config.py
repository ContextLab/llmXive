"""
Configuration for linting (ruff) and formatting (black) tools.

This module provides a centralized configuration for code quality tools
used in the PROJ-753 project. It defines the settings for ruff and black
to ensure consistent code style and linting across the project.

Note: Actual tool configuration is stored in pyproject.toml and 
.ruff.toml files, but this module documents the project's standards.
"""

# Ruff configuration (mirrors .ruff.toml)
RUFF_CONFIG = {
    "target_version": "py311",
    "line_length": 88,
    "select": [
        "E",  # pycodestyle errors
        "W",  # pycodestyle warnings
        "F",  # Pyflakes
        "I",  # isort
        "B",  # flake8-bugbear
        "C4", # flake8-comprehensions
        "UP", # pyupgrade
    ],
    "ignore": [
        "E501",  # line too long (handled by black)
        "B008",  # do not perform function calls in argument defaults
    ],
    "exclude": [
        ".git",
        "__pycache__",
        ".venv",
        "data",
        "reports",
    ],
}

# Black configuration (mirrors pyproject.toml)
BLACK_CONFIG = {
    "line_length": 88,
    "target_version": ["py311"],
    "skip_string_normalization": False,
    "exclude": r"/(\.git|__pycache__|\.venv|data|reports)/",
}

def get_ruff_command():
    """Return the ruff command with project-specific flags."""
    return "ruff check --config .ruff.toml code/ tests/"

def get_black_command():
    """Return the black command with project-specific flags."""
    return "black --config pyproject.toml code/ tests/"

def get_ruff_format_command():
    """Return the ruff format command for formatting."""
    return "ruff format --config .ruff.toml code/ tests/"

def run_lint():
    """Execute ruff linting on the project codebase."""
    import subprocess
    import sys
    
    try:
        result = subprocess.run(
            ["ruff", "check", "code/", "tests/"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: ruff not found. Install with: pip install ruff")
        return False
    except Exception as e:
        print(f"Error running ruff: {e}")
        return False

def run_format():
    """Execute black formatting on the project codebase."""
    import subprocess
    import sys
    
    try:
        result = subprocess.run(
            ["black", "code/", "tests/"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: black not found. Install with: pip install black")
        return False
    except Exception as e:
        print(f"Error running black: {e}")
        return False

if __name__ == "__main__":
    print("Running linter...")
    lint_success = run_lint()
    print(f"\nLinting {'passed' if lint_success else 'failed'}")
    
    print("\nRunning formatter...")
    format_success = run_format()
    print(f"\nFormatting {'completed' if format_success else 'failed'}")
    
    if lint_success and format_success:
        print("\n✓ All code quality checks passed!")
        exit(0)
    else:
        print("\n✗ Code quality checks failed. Please fix the issues above.")
        exit(1)
