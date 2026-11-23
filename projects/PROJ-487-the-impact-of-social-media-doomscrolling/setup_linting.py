"""
Task T006: Configure linting (flake8/black) and formatting tools.
Creates configuration files and installs tools if missing.
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

# Import logging utility from the project's existing structure
# Note: The API surface lists `code/utils/logging.py` with `get_logger`
# However, to ensure this script runs standalone for setup, we define a minimal fallback
# if the import fails, but prefer the project's logger.
try:
    sys.path.insert(0, str(Path(__file__).parent / "code"))
    from utils.logging import get_logger
    logger = get_logger("setup_linting")
except ImportError:
    # Fallback for standalone execution if utils aren't ready yet
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("setup_linting")

def create_gitignore_entry(root: Path) -> None:
    """Ensure .gitignore includes standard Python linting/venv ignores."""
    gitignore_path = root / ".gitignore"
    entries = [
        ".venv/",
        "venv/",
        "__pycache__/",
        "*.pyc",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        ".mypy_cache/",
    ]
    
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        for entry in entries:
            if entry not in content:
                with open(gitignore_path, "a") as f:
                    f.write(f"\n# Added by setup_linting.py\n{entry}\n")
                logger.info(f"Added {entry} to .gitignore")
    else:
        with open(gitignore_path, "w") as f:
            f.write("\n".join(entries))
            f.write("\n")
        logger.info(f"Created .gitignore with entries")

def create_flake8_config(root: Path) -> None:
    """Create .flake8 configuration file."""
    config_path = root / ".flake8"
    content = """[flake8]
max-line-length = 100
ignore = E203, W503, E731
exclude =
    .git,
    __pycache__,
    .venv,
    venv,
    build,
    dist,
    *.egg-info
per-file-ignores =
    */__init__.py: F401
    */tests/*.py: E701, E702, W503, S101
max-complexity = 15
"""
    with open(config_path, "w") as f:
        f.write(content)
    logger.info(f"Created {config_path}")

def create_black_config(root: Path) -> None:
    """Create Black configuration in pyproject.toml."""
    pyproject_path = root / "pyproject.toml"
    black_section = """
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']
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
    
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" not in content:
            with open(pyproject_path, "a") as f:
                f.write(black_section)
            logger.info(f"Appended [tool.black] to {pyproject_path}")
        else:
            logger.info(f"[tool.black] already exists in {pyproject_path}")
    else:
        # Create minimal pyproject.toml if it doesn't exist
        with open(pyproject_path, "w") as f:
            f.write("""[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "proj-487-the-impact-of-social-media-doomscrolling"
version = "0.1.0"
description = "Analysis of aggregate negative news publication volume on anticipatory anxiety"
requires-python = ">=3.9"
dependencies = [
    "pandas",
    "numpy",
    "statsmodels",
    "requests",
    "scikit-learn",
    "matplotlib",
    "seaborn",
    "pyyaml",
    "pytrends",
]
""")
            f.write(black_section)
        logger.info(f"Created {pyproject_path} with Black config")

def create_isort_config(root: Path) -> None:
    """Add isort configuration to pyproject.toml."""
    pyproject_path = root / "pyproject.toml"
    isort_section = """
[tool.isort]
profile = "black"
line_length = 100
known_first_party = ["data", "utils", "tests", "config"]
known_third_party = ["pandas", "numpy", "statsmodels", "requests", "sklearn", "matplotlib", "seaborn", "yaml", "pytrends"]
skip = [".git", ".venv", "venv", "build", "dist"]
"""
    
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.isort]" not in content:
            with open(pyproject_path, "a") as f:
                f.write(isort_section)
            logger.info(f"Appended [tool.isort] to {pyproject_path}")
        else:
            logger.info(f"[tool.isort] already exists in {pyproject_path}")

def install_linting_tools() -> None:
    """Install flake8, black, isort, and pytest if not present."""
    tools = ["flake8", "black", "isort", "pytest", "pytest-cov"]
    for tool in tools:
        logger.info(f"Checking for {tool}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "show", tool],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"{tool} is already installed.")
        except subprocess.CalledProcessError:
            logger.info(f"Installing {tool}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", tool],
                check=True
            )
    logger.info("Linting tools installation complete.")

def main() -> None:
    """Main entry point for T006."""
    logger.info("Starting T006: Configure linting and formatting tools.")
    
    # Determine project root (parent of code/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent
    
    # Create config files
    create_gitignore_entry(project_root)
    create_flake8_config(project_root)
    create_black_config(project_root)
    create_isort_config(project_root)
    
    # Install tools
    install_linting_tools()
    
    logger.info("T006 completed successfully. Config files created and tools installed.")

if __name__ == "__main__":
    main()