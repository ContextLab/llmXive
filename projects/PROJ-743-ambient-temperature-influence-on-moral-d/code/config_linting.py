import os
import sys
import tomli
import tomli_w
from pathlib import Path

from config import get_path_env_override

def ensure_pyproject_toml(project_root: Path) -> bool:
    """
    Ensure pyproject.toml exists and contains [tool.black] and [tool.ruff] sections.
    Returns True if the file is valid and contains the required sections.
    """
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        # Create a minimal pyproject.toml with required sections
        config = {
            "project": {
                "name": "ambient-temp-moral-speed",
                "version": "0.1.0",
                "dependencies": [
                    "pandas",
                    "numpy",
                    "scikit-learn",
                    "statsmodels",
                    "cdsapi",
                    "pyarrow",
                    "matplotlib",
                    "seaborn",
                    "geopandas",
                    "shapely",
                    "ruff",
                    "black",
                    "tomli",
                    "tomli-w",
                ],
            },
            "tool": {
                "black": {
                    "line-length": 88,
                    "target-version": ["py310"],
                },
                "ruff": {
                    "line-length": 88,
                    "target-version": "py310",
                    "select": ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"],
                    "ignore": [],
                    "exclude": [
                        ".git",
                        "__pycache__",
                        ".venv",
                        "venv",
                        "build",
                        "dist",
                        "*.egg-info",
                    ],
                },
            },
        }
        with open(pyproject_path, "wb") as f:
            tomli_w.dump(config, f)
        return True

    # File exists, check for required sections
    try:
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)

        tool = config.get("tool", {})
        if "black" not in tool or "ruff" not in tool:
            # Update existing config to include missing sections
            if "tool" not in config:
                config["tool"] = {}
            if "black" not in config["tool"]:
                config["tool"]["black"] = {
                    "line-length": 88,
                    "target-version": ["py310"],
                }
            if "ruff" not in config["tool"]:
                config["tool"]["ruff"] = {
                    "line-length": 88,
                    "target-version": "py310",
                    "select": ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"],
                    "ignore": [],
                    "exclude": [
                        ".git",
                        "__pycache__",
                        ".venv",
                        "venv",
                        "build",
                        "dist",
                        "*.egg-info",
                    ],
                }
            with open(pyproject_path, "wb") as f:
                tomli_w.dump(config, f)
            return True

        return True
    except Exception as e:
        print(f"Error reading/writing pyproject.toml: {e}")
        return False

def ensure_ruff_config(project_root: Path) -> bool:
    """
    Ensure ruff.toml exists with proper configuration.
    Note: ruff.toml is deprecated in favor of pyproject.toml [tool.ruff],
    but we create it for compatibility with older workflows.
    """
    ruff_path = project_root / "ruff.toml"

    config_content = """# Ruff configuration
line-length = 88
target-version = "py310"

[lint]
select = [
    "E",   # pycodestyle errors
    "F",   # Pyflakes
    "W",   # pycodestyle warnings
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "SIM", # flake8-simplify
]
ignore = []

[lint.per-file-ignores]
"__init__.py" = ["F401"]
"conftest.py" = ["F401"]
"tests/*" = ["S101", "ARG"]

[lint.isort]
known-first-party = ["code"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""

    with open(ruff_path, "w") as f:
        f.write(config_content)
    return True

def ensure_flake8_config(project_root: Path) -> bool:
    """
    Ensure .flake8 config exists (for compatibility, though ruff is preferred).
    """
    flake8_path = project_root / ".flake8"

    config_content = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,.venv,venv,build,dist,*.egg-info
ignore = E203,E266,W503
select = E,F,W,C90,I,N,UP,B,C4,SIM
"""
    with open(flake8_path, "w") as f:
        f.write(config_content)
    return True

def main() -> int:
    """
    Main entry point for T009: Configure Linting and Formatting.
    Creates/updates pyproject.toml, ruff.toml, and .flake8.
    """
    project_root = Path(get_path_env_override("PROJECT_ROOT", "."))

    success = True

    if not ensure_pyproject_toml(project_root):
        print("Failed to ensure pyproject.toml")
        success = False

    if not ensure_ruff_config(project_root):
        print("Failed to ensure ruff.toml")
        success = False

    if not ensure_flake8_config(project_root):
        print("Failed to ensure .flake8")
        success = False

    if success:
        print("Linting and formatting configuration created successfully.")
    else:
        print("Some configuration steps failed.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())