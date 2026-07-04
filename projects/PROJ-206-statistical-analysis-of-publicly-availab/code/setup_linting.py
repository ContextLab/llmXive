"""
Task T003: Configure linting (ruff) and formatting (black) tools.

This script:
1. Verifies that 'ruff' and 'black' are installed.
2. Creates a 'pyproject.toml' file at the project root with configuration
   for both tools, tailored to the project's structure (src/, tests/).
3. Ensures the configuration includes sensible defaults for a scientific
   Python project (line length 88, target version py39+).
"""
import os
import subprocess
import sys
from pathlib import Path

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and available in the environment."""
    try:
        subprocess.run(
            [sys.executable, "-m", tool_name, "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool_name: str) -> None:
    """Install a tool if it is missing."""
    print(f"Installing {tool_name}...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", tool_name],
        check=True,
    )

def create_pyproject_config() -> None:
    """Create or update pyproject.toml with linting and formatting configs."""
    root = Path(__file__).resolve().parent.parent
    config_path = root / "pyproject.toml"

    config_content = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "statistical-poll-aggregation"
version = "0.1.0"
description = "Statistical analysis of publicly available election poll aggregates"
requires-python = ">=3.9"
dependencies = [
    "pandas",
    "numpy",
    "scipy",
    "pymc",
    "arviz",
    "requests",
    "pyyaml",
    "statsmodels",
    "pytest",
]

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    # The following are specific to Black, you probably don't want those.
    | build
    | dist
    | .eggs
    | venv
    | .venv
    | __pycache__
)/
'''

[tool.ruff]
line-length = 88
target-version = "py39"
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
    "C901", # too complex
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"] # Allow unused imports in init files

[tool.ruff.isort]
known-first-party = ["statistical_poll_aggregation"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"
"""

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)

    print(f"Configuration written to {config_path}")

def main() -> None:
    """Main entry point for T003."""
    print("Starting T003: Configuring linting and formatting tools...")

    tools = ["ruff", "black"]
    missing_tools = [t for t in tools if not check_tool_installed(t)]

    if missing_tools:
        for tool in missing_tools:
            install_tool(tool)
        print("All tools installed successfully.")
    else:
        print("All required tools are already installed.")

    create_pyproject_config()
    print("T003 completed successfully.")

if __name__ == "__main__":
    main()