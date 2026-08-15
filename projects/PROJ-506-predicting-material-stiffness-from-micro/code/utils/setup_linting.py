import subprocess
import sys
import tomllib
from pathlib import Path
from typing import List, Tuple, Optional


def check_command_available(command: str) -> Tuple[bool, str]:
    """Check if a command is available in the system PATH."""
    try:
        subprocess.run(
            [command, "--version"],
            capture_output=True,
            check=True,
            text=True,
            timeout=10,
        )
        return True, f"{command} is available."
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, f"{command} is not installed or not in PATH."


def create_pyproject_config(project_root: Path) -> None:
    """Create or update pyproject.toml with ruff and black configurations."""
    pyproject_path = project_root / "pyproject.toml"

    # Define the configuration sections
    ruff_config = """
[tool.ruff]
# Same as Black.
line-length = 88
indent-width = 4

[tool.ruff.lint]
# Enable Pyflakes (`F`) and a subset of the pycodestyle (`E`)  codes by default.
select = ["E4", "E7", "E9", "F", "I"]
ignore = []

# Allow fix for all enabled rules (when `--fix`) is provided.
fixable = ["ALL"]
unfixable = []

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.format]
# Like Black, use double quotes for strings.
quote-style = "double"

# Like Black, indent with spaces, rather than tabs.
indent-style = "space"

# Like Black, respect magic trailing commas.
skip-magic-trailing-comma = false

# Like Black, automatically detect the appropriate line ending.
line-ending = "auto"
"""

    black_config = """
[tool.black]
line-length = 88
target-version = ['py310']
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
    \\)
)/
'''
"""

    # Check if file exists and read content
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        # Simple check to see if sections already exist
        has_ruff = "[tool.ruff" in content
        has_black = "[tool.black" in content

        if has_ruff and has_black:
            print("pyproject.toml already contains ruff and black configurations.")
            return

        # Append missing sections
        with pyproject_path.open("a") as f:
            if not has_ruff:
                f.write(ruff_config)
            if not has_black:
                f.write(black_config)
    else:
        # Create new file with both configurations
        with pyproject_path.open("w") as f:
            f.write(ruff_config.strip() + "\n\n")
            f.write(black_config.strip() + "\n")

    print(f"Successfully updated {pyproject_path} with linting and formatting configurations.")


def validate_config_files(project_root: Path) -> List[str]:
    """Validate that configuration files exist and are readable."""
    issues = []
    config_files = ["pyproject.toml"]

    for config_file in config_files:
        file_path = project_root / config_file
        if not file_path.exists():
            issues.append(f"Missing configuration file: {config_file}")
        else:
            try:
                with file_path.open("rb") as f:
                    tomllib.load(f)
            except Exception as e:
                issues.append(f"Invalid TOML in {config_file}: {str(e)}")

    return issues


def main() -> int:
    """Main entry point for setting up linting and formatting tools."""
    project_root = Path(__file__).resolve().parent.parent

    print("Setting up linting (ruff/flake8) and formatting (black) tools...")

    # Check for ruff
    ruff_available, ruff_msg = check_command_available("ruff")
    print(f"  Ruff: {ruff_msg}")

    # Check for black
    black_available, black_msg = check_command_available("black")
    print(f"  Black: {black_msg}")

    if not ruff_available:
        print("  Recommendation: Install ruff with `pip install ruff`")
    if not black_available:
        print("  Recommendation: Install black with `pip install black`")

    # Create/update pyproject.toml
    create_pyproject_config(project_root)

    # Validate configuration
    issues = validate_config_files(project_root)
    if issues:
        print("\nConfiguration validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("\nLinting and formatting configuration complete.")
    print("You can now run:")
    print("  ruff check .       # Lint code")
    print("  ruff format .      # Format code")
    print("  black .            # Alternative formatter")

    return 0


if __name__ == "__main__":
    sys.exit(main())