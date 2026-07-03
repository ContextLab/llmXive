"""
Setup script for development environment configuration.
Configures linting (ruff) and formatting (black) tools.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> None:
    """Run a shell command and raise on failure."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True, capture_output=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def ensure_package(package: str) -> None:
    """Ensure a package is installed."""
    print(f"Ensuring {package} is installed...")
    run_command([sys.executable, "-m", "pip", "install", package])


def main() -> None:
    """Install and configure dev tools."""
    # Install tools
    ensure_package("ruff")
    ensure_package("black")

    project_root = Path(__file__).parent.parent

    # Create ruff.toml configuration
    ruff_config = project_root / "ruff.toml"
    if not ruff_config.exists():
        config_content = """
# Ruff configuration for llmXive project
target-version = "py311"

[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["code", "tests"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
        ruff_config.write_text(config_content.strip())
        print(f"Created {ruff_config}")
    else:
        print(f"{ruff_config} already exists, skipping creation.")

    # Create pyproject.toml for black if it doesn't exist
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        black_config = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\(
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
    \\)/
)
'''
"""
        pyproject.write_text(black_config.strip())
        print(f"Created {pyproject}")
    else:
        print(f"{pyproject} already exists, skipping creation.")

    print("\nDevelopment environment setup complete.")
    print("Run 'ruff check .' to lint and 'black .' to format.")


if __name__ == "__main__":
    main()