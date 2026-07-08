import os
import subprocess
import sys
from pathlib import Path


def get_flake8_command():
    """
    Constructs the command list for running flake8 with project-specific configuration.
    Returns a list of strings suitable for subprocess.run().
    """
    return [
        sys.executable, "-m", "flake8",
        "--max-line-length=88",
        "--extend-ignore=E203,W503",
        "--exclude=.git,__pycache__,build,dist,venv,env,.venv",
        "code/", "tests/"
    ]


def get_black_command():
    """
    Constructs the command list for running Black with project-specific configuration.
    Returns a list of strings suitable for subprocess.run().
    """
    return [
        sys.executable, "-m", "black",
        "--line-length", "88",
        "--exclude", r"/(\.git|__pycache__|build|dist|venv|env|\.venv)/",
        "code/", "tests/"
    ]


def run_linter():
    """
    Executes the flake8 linter on the project code.
    Prints the output to stdout and returns the exit code.
    """
    cmd = get_flake8_command()
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: flake8 not found. Please ensure it is installed.", file=sys.stderr)
        return 1


def run_formatter():
    """
    Executes the Black formatter on the project code.
    Prints the output to stdout and returns the exit code.
    """
    cmd = get_black_command()
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Please ensure it is installed.", file=sys.stderr)
        return 1


def create_config_files():
    """
    Creates configuration files for flake8 (.flake8) and Black (pyproject.toml section)
    if they do not already exist in the project root.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Create .flake8
    flake8_path = project_root / ".flake8"
    if not flake8_path.exists():
        content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,venv,env,.venv
"""
        with open(flake8_path, "w") as f:
            f.write(content)
        print(f"Created {flake8_path}")
    else:
        print(f"{flake8_path} already exists.")

    # Create/Update pyproject.toml for Black
    pyproject_path = project_root / "pyproject.toml"
    black_section_exists = False
    if pyproject_path.exists():
        with open(pyproject_path, "r") as f:
            content = f.read()
            if "[tool.black]" in content:
                black_section_exists = True

    if not black_section_exists:
        black_config = """
[tool.black]
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
        # Append to existing or create new
        mode = "a" if pyproject_path.exists() else "w"
        with open(pyproject_path, mode) as f:
            if mode == "w" and pyproject_path.exists():
                pass # Should not happen if logic is correct, but safe guard
            f.write(black_config)
        print(f"Added Black configuration to {pyproject_path}")
    else:
        print(f"Black configuration already exists in {pyproject_path}.")


def main():
    """
    Entry point for the linting configuration script.
    Allows running linter, formatter, or creating config files via CLI.
    Usage: python code/linting_config.py [lint|format|setup]
    """
    if len(sys.argv) < 2:
        print("Usage: python code/linting_config.py [lint|format|setup]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "setup":
        create_config_files()
    elif command == "lint":
        exit_code = run_linter()
        sys.exit(exit_code)
    elif command == "format":
        exit_code = run_formatter()
        sys.exit(exit_code)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()