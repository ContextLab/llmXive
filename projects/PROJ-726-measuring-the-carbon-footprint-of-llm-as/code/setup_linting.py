"""
Setup script for linting (ruff) and formatting (black) tools.
Generates configuration files and provides helper functions to run them.
"""
import os
import subprocess
import sys
from pathlib import Path


def write_config_file(path: Path, content: str) -> None:
    """Write configuration content to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created configuration file: {path}")


def setup_black_config(project_root: Path) -> None:
    """Create pyproject.toml with Black configuration."""
    config_path = project_root / "pyproject.toml"
    content = """[tool.black]
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
"""
    # Check if file exists and append if needed, or create new
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            existing = f.read()
        if "[tool.black]" not in existing:
            with open(config_path, "a", encoding="utf-8") as f:
                f.write("\n" + content)
            print(f"Appended Black config to {config_path}")
        else:
            print(f"Black config already exists in {config_path}")
    else:
        write_config_file(config_path, content)


def setup_ruff_config(project_root: Path) -> None:
    """Create .ruff.toml with Ruff configuration."""
    config_path = project_root / ".ruff.toml"
    content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[lint.isort]
known-first-party = ["code"]
force-sort-within-sections = true

[format]
line-length = 88
"""
    write_config_file(config_path, content)


def run_format(project_root: Path) -> int:
    """Run Black formatter on the code directory."""
    print("Running Black formatter...")
    code_dir = project_root / "code"
    try:
        subprocess.run(
            [sys.executable, "-m", "black", str(code_dir)],
            check=True,
            cwd=project_root,
        )
        print("Black formatting completed successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Black formatting failed: {e}")
        return 1
    except FileNotFoundError:
        print("Error: 'black' is not installed. Run: pip install black")
        return 1


def run_lint(project_root: Path) -> int:
    """Run Ruff linter on the code directory."""
    print("Running Ruff linter...")
    code_dir = project_root / "code"
    try:
        subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_dir)],
            check=True,
            cwd=project_root,
        )
        print("Ruff linting passed.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Ruff linting found issues or failed: {e}")
        return 1
    except FileNotFoundError:
        print("Error: 'ruff' is not installed. Run: pip install ruff")
        return 1


def main() -> int:
    """Main entry point for setup_linting script."""
    project_root = Path(__file__).resolve().parent.parent
    print(f"Project root detected at: {project_root}")

    print("\n--- Configuring Black ---")
    setup_black_config(project_root)

    print("\n--- Configuring Ruff ---")
    setup_ruff_config(project_root)

    print("\n--- Configuration complete ---")
    print("To format code: python code/setup_linting.py format")
    print("To lint code: python code/setup_linting.py lint")
    print("To do both: python code/setup_linting.py check")

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "format":
            return run_format(project_root)
        elif command == "lint":
            return run_lint(project_root)
        elif command == "check":
            r = run_format(project_root)
            if r != 0:
                return r
            return run_lint(project_root)
        else:
            print(f"Unknown command: {command}")
            print("Usage: python code/setup_linting.py [format|lint|check]")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
