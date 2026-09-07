from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path


def run_command(command: list[str], description: str) -> bool:
    """
    Execute a shell command and return True if successful.

    Args:
        command: List of command arguments.
        description: Human-readable description of the action for logging.

    Returns:
        True if the command succeeded (exit code 0), False otherwise.
    """
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=False,
            text=True,
            env=os.environ
        )
        print(f"Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {description} failed with exit code {e.returncode}")
        return False


def main() -> None:
    """
    Main entry point to configure linting (ruff) and formatting (black) tools.

    This function:
    1. Installs ruff and black via pip if not already present.
    2. Initializes a default ruff configuration file (.ruff.toml).
    3. Initializes a default black configuration file (pyproject.toml section).
    4. Runs a dry-run lint check to verify configuration validity.
    """
    project_root = Path(__file__).parent.parent
    print(f"Project root: {project_root}")

    # 1. Install dependencies
    deps = [
        ["pip", "install", "-U", "ruff", "black"],
    ]

    for cmd in deps:
        if not run_command(cmd, f"Installing {' '.join(cmd[2:])}"):
            sys.exit(1)

    # 2. Create .ruff.toml configuration
    ruff_config_path = project_root / ".ruff.toml"
    ruff_config_content = """[lint]
# Select common rules: E (pyflakes), F (pycodestyle), W (warnings), I (isort), N (pep8-naming), UP (pyupgrade)
select = ["E", "F", "W", "I", "N", "UP", "D"]

# Ignore specific rules that might be too strict for this project initially
ignore = [
    "D100", # Missing docstring in public module
    "D104", # Missing docstring in public package
    "D203", # 1 blank line required before class docstring (conflicts with D211)
    "D213", # Multi-line docstring summary should start at the second line (conflicts with D212)
    "D401", # First line should be in imperative mood (too strict for some docs)
]

# Allow automatic fixing for most issues
fixable = ["ALL"]
unfixable = []

[lint.per-file-ignores]
# Ignore docstring requirements for test files and scripts that are mostly glue code
"tests/**" = ["D"]
"scripts/**" = ["D"]

[lint.pydocstyle]
convention = "google"

[format]
# Use double quotes for strings
quote-style = "double"

# Indent with spaces
indent-style = "space"

# Respect magic trailing commas
skip-magic-trailing-comma = false

# Line length
line-length = 88
"""

    with open(ruff_config_path, "w", encoding="utf-8") as f:
        f.write(ruff_config_content)
    print(f"Created {ruff_config_path}")

    # 3. Update pyproject.toml for Black configuration
    pyproject_path = project_root / "pyproject.toml"
    black_section = """
[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
include = '\\.pyi?$'
"""

    if pyproject_path.exists():
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "[tool.black]" not in content:
            with open(pyproject_path, "a", encoding="utf-8") as f:
                f.write(black_section)
            print(f"Updated {pyproject_path} with Black configuration")
        else:
            print(f"Black configuration already exists in {pyproject_path}")
    else:
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(black_section)
        print(f"Created {pyproject_path} with Black configuration")

    # 4. Verify configuration by running a dry check on the code directory
    code_dir = project_root / "code"
    if code_dir.exists():
        print("\nVerifying ruff configuration...")
        if not run_command(
            ["ruff", "check", str(code_dir)],
            "Ruff check (dry-run)"
        ):
            print("Warning: Ruff check found issues. This is expected if code needs fixing.")
            # We don't fail here, as the task is to configure, not fix all existing issues yet
        else:
            print("Ruff check passed.")

        print("\nVerifying black configuration...")
        if not run_command(
            ["black", "--check", "--diff", str(code_dir)],
            "Black check (dry-run)"
        ):
            print("Warning: Black check found formatting issues. This is expected if code needs formatting.")
        else:
            print("Black check passed.")
    else:
        print(f"Warning: Code directory {code_dir} not found, skipping verification checks.")

    print("\nLinting and formatting tools configured successfully.")


if __name__ == "__main__":
    main()