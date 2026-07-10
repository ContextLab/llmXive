import subprocess
import sys
from pathlib import Path
import shutil

def run_command(cmd: list[str], cwd: Path | None = None) -> bool:
    """
    Execute a shell command and return True if successful, False otherwise.
    """
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(cmd)}")
        print(f"Return code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
        return False

def main() -> None:
    """
    Configure linting (ruff) and formatting (black) tools.
    
    This script:
    1. Installs ruff and black if not present
    2. Creates a pyproject.toml configuration for ruff and black
    3. Creates a .pre-commit-config.yaml for pre-commit hooks
    """
    project_root = Path.cwd()
    
    # Ensure tools are installed
    print("Checking/installing required tools...")
    if not run_command([sys.executable, "-m", "pip", "install", "ruff", "black", "pre-commit"]):
        print("Failed to install tools. Please install manually: pip install ruff black pre-commit")
        sys.exit(1)
    
    # Create pyproject.toml configuration
    pyproject_path = project_root / "pyproject.toml"
    
    if pyproject_path.exists():
        # Read existing content
        content = pyproject_path.read_text()
        # Check if we already have tool configurations
        has_ruff = "[tool.ruff]" in content
        has_black = "[tool.black]" in content
        
        if has_ruff and has_black:
            print("Ruff and Black configurations already exist in pyproject.toml")
        else:
            # Append missing configurations
            print("Appending missing configurations to pyproject.toml")
            with open(pyproject_path, "a") as f:
                if not has_ruff:
                    f.write("\n\n[tool.ruff]\n")
                    f.write("line-length = 88\n")
                    f.write("target-version = \"py311\"\n")
                    f.write("select = [\"E\", \"F\", \"W\", \"I\", \"N\", \"UP\", \"B\", \"C4\", \"ARG\", \"SIM\"]\n")
                    f.write("ignore = [\"E501\", \"B008\"]\n")
                    f.write("\n[tool.ruff.per-file-ignores]\n")
                    f.write("\"__init__.py\" = [\"F401\"]\n")
                    f.write("\"tests/*\" = [\"S101\"]\n")
                
                if not has_black:
                    f.write("\n\n[tool.black]\n")
                    f.write("line-length = 88\n")
                    f.write("target-version = ['py311']\n")
                    f.write("include = '\\.pyi?$'\n")
                    f.write("exclude = '''\n")
                    f.write("    /(\n")
                    f.write("        \\.git\n")
                    f.write("        | \\.hg\n")
                    f.write("        | \\.mypy_cache\n")
                    f.write("        | \\.tox\n")
                    f.write("        | \\.venv\n")
                    f.write("        | _build\n")
                    f.write("        | buck-out\n")
                    f.write("        | build\n")
                    f.write("        | dist\n")
                    f.write("    )/\n")
                    f.write("'''\n")
    else:
        # Create new pyproject.toml
        print("Creating new pyproject.toml with tool configurations")
        with open(pyproject_path, "w") as f:
            f.write("[build-system]\n")
            f.write("requires = [\"setuptools>=45\", \"wheel\"]\n")
            f.write("build-backend = \"setuptools.build_meta\"\n")
            f.write("\n")
            f.write("[project]\n")
            f.write("name = \"llmXive-project\"\n")
            f.write("version = \"0.1.0\"\n")
            f.write("description = \"LLM-driven science pipeline\"\n")
            f.write("requires-python = \">=3.11\"\n")
            f.write("\n")
            f.write("[tool.ruff]\n")
            f.write("line-length = 88\n")
            f.write("target-version = \"py311\"\n")
            f.write("select = [\"E\", \"F\", \"W\", \"I\", \"N\", \"UP\", \"B\", \"C4\", \"ARG\", \"SIM\"]\n")
            f.write("ignore = [\"E501\", \"B008\"]\n")
            f.write("\n[tool.ruff.per-file-ignores]\n")
            f.write("\"__init__.py\" = [\"F401\"]\n")
            f.write("\"tests/*\" = [\"S101\"]\n")
            f.write("\n[tool.black]\n")
            f.write("line-length = 88\n")
            f.write("target-version = ['py311']\n")
            f.write("include = '\\.pyi?$'\n")
            f.write("exclude = '''\n")
            f.write("    /(\n")
            f.write("        \\.git\n")
            f.write("        | \\.hg\n")
            f.write("        | \\.mypy_cache\n")
            f.write("        | \\.tox\n")
            f.write("        | \\.venv\n")
            f.write("        | _build\n")
            f.write("        | buck-out\n")
            f.write("        | build\n")
            f.write("        | dist\n")
            f.write("    )/\n")
            f.write("'''\n")
    
    # Create .pre-commit-config.yaml
    precommit_path = project_root / ".pre-commit-config.yaml"
    if not precommit_path.exists():
        print("Creating .pre-commit-config.yaml")
        with open(precommit_path, "w") as f:
            f.write("repos:\n")
            f.write("  - repo: https://github.com/psf/black\n")
            f.write("    rev: 23.12.1\n")
            f.write("    hooks:\n")
            f.write("      - id: black\n")
            f.write("        language_version: python3.11\n")
            f.write("  - repo: https://github.com/astral-sh/ruff-pre-commit\n")
            f.write("    rev: v0.1.9\n")
            f.write("    hooks:\n")
            f.write("      - id: ruff\n")
            f.write("        args: [--fix]\n")
            f.write("      - id: ruff-format\n")
    else:
        print(".pre-commit-config.yaml already exists")
    
    # Initialize pre-commit hooks
    print("Initializing pre-commit hooks...")
    if run_command(["pre-commit", "install"], cwd=project_root):
        print("Pre-commit hooks installed successfully")
    else:
        print("Could not install pre-commit hooks. Run 'pre-commit install' manually.")
    
    # Create .ruff.toml for additional overrides if needed (optional)
    ruff_config_path = project_root / ".ruff.toml"
    if not ruff_config_path.exists():
        print("Creating .ruff.toml for additional overrides")
        with open(ruff_config_path, "w") as f:
            f.write("# Additional Ruff overrides\n")
            f.write("extend-ignore = [\n")
            f.write("    \"D\",  # Ignore docstring conventions\n")
            f.write("]\n")
    
    print("Linting and formatting configuration complete!")
    print("Run 'black code/' to format code")
    print("Run 'ruff check code/' to lint code")
    print("Run 'pre-commit run --all-files' to check all files")
