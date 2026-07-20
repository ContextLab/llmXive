import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str]) -> None:
    """
    Execute a shell command and raise an error if it fails.
    
    Args:
        cmd: List of command arguments to execute.
    """
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

def main() -> None:
    """
    Install and configure linting (ruff) and formatting (black) tools.
    
    This function:
    1. Installs ruff and black via pip.
    2. Creates a pyproject.toml with default configurations for both tools
       if one does not already exist or if the sections are missing.
    """
    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"

    # 1. Install tools
    print("Installing linting and formatting tools...")
    run_command([sys.executable, "-m", "pip", "install", "ruff", "black"])

    # 2. Create or update pyproject.toml
    config_content = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'

[tool.ruff]
line-length = 88
target-version = "py311"
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[tool.ruff.isort]
known-first-party = ["download", "models", "metrics", "stratify", "recalibration", "run_pipeline"]
"""

    if not pyproject_path.exists():
        pyproject_path.write_text(config_content.strip())
        print(f"Created {pyproject_path} with ruff and black configuration.")
    else:
        content = pyproject_path.read_text()
        if "[tool.black]" not in content or "[tool.ruff]" not in content:
            # Append missing sections
            pyproject_path.write_text(content.rstrip() + "\n" + config_content.strip())
            print(f"Updated {pyproject_path} with missing ruff/black configuration.")
        else:
            print(f"{pyproject_path} already contains ruff and black configuration.")

    print("Linting and formatting setup complete.")

if __name__ == "__main__":
    main()