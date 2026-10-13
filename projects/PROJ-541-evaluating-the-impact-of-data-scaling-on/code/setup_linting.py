"""
Setup linting and formatting tools for the project.
Creates configuration files for Ruff, Flake8, and Black.
"""
import sys
import subprocess
from pathlib import Path


def write_ruff_config(path: Path):
    """Write a basic Ruff configuration."""
    content = """[tool.ruff]
line-length = 88
select = ["E", "F", "W", "C90"]
ignore = []
exclude = ["__pycache__", "data", "results", "logs"]
"""
    path.write_text(content)


def write_flake8_config(path: Path):
    """Write a basic Flake8 configuration."""
    content = """[flake8]
max-line-length = 88
exclude = __pycache__,data,results,logs
"""
    path.write_text(content)


def write_black_config(pyproject_path: Path):
    """Ensure a [tool.black] section exists in pyproject.toml."""
    if pyproject_path.exists():
        text = pyproject_path.read_text()
        if "[tool.black]" not in text:
            with pyproject_path.open("a") as f:
                f.write(
"\n[tool.black]\\nline-length = 88\\nskip-string-normalization = false\\n"
                )
    else:
        content = """[tool.black]
line-length = 88
skip-string-normalization = false
"""
        pyproject_path.write_text(content)


def install_tools():
    """Install linting/formatting tools from the pinned requirements."""
    req_path = Path(__file__).parent / "requirements.txt"
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_path)])


def main():
    """Create config files and optionally install the tools."""
    project_root = Path(__file__).parent
    
    # Config files
    write_ruff_config(project_root / "ruff.toml")
    write_flake8_config(project_root / ".flake8")
    write_black_config(project_root / "pyproject.toml")
    
    # Uncomment the following line if you want the script to install the tools automatically
    # install_tools()
    
    print("Linting and formatting configuration files have been set up.")


if __name__ == "__main__":
    main()
