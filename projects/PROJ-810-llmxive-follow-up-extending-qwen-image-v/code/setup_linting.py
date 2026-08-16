import subprocess
import sys
import os
from pathlib import Path
import tomli_w
import tomli

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and available in the environment."""
    try:
        subprocess.run([tool_name, "--version"], check=True, capture_output=True, text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tools() -> None:
    """Install linting and formatting tools if not present."""
    tools = [
        ("ruff", "ruff"),
        ("black", "black"),
    ]
    for display_name, cmd in tools:
        if not check_tool_installed(cmd):
            print(f"Installing {display_name}...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-U", cmd], check=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to install {display_name}: {e}")

def verify_config_files(project_root: Path) -> None:
    """Create or verify configuration files for linting and formatting."""
    # Create pyproject.toml with tool configurations if it doesn't exist
    pyproject_path = project_root / "pyproject.toml"
    
    if not pyproject_path.exists():
        config = {
            "tool": {
                "black": {
                    "line-length": 88,
                    "target-version": ["py310"],
                    "include": r'\.pyi?$'
                },
                "ruff": {
                    "target-version": "py310",
                    "line-length": 88,
                    "select": [
                        "E",   # pycodestyle errors
                        "W",   # pycodestyle warnings
                        "F",   # Pyflakes
                        "I",   # isort
                        "B",   # flake8-bugbear
                        "C4",  # flake8-comprehensions
                        "UP",  # pyupgrade
                    ],
                    "ignore": [
                        "E501", # Line too long (handled by black)
                    ],
                    "exclude": [
                        ".git",
                        "__pycache__",
                        ".eggs",
                        "*.egg-info",
                        "build",
                        "dist",
                        "data",
                        "cache"
                    ]
                }
            }
        }
        
        with open(pyproject_path, "wb") as f:
            tomli_w.dump(config, f)
        print(f"Created {pyproject_path}")
    else:
        # Verify configuration exists
        try:
            with open(pyproject_path, "rb") as f:
                config = tomli.load(f)
            if "tool" not in config or "black" not in config["tool"]:
                raise ValueError("Black configuration missing in pyproject.toml")
            if "tool" not in config or "ruff" not in config["tool"]:
                raise ValueError("Ruff configuration missing in pyproject.toml")
            print(f"Verified {pyproject_path}")
        except Exception as e:
            raise RuntimeError(f"Invalid pyproject.toml configuration: {e}")

def run_lint_check(project_root: Path) -> int:
    """Run ruff linter on the project."""
    try:
        result = subprocess.run(
            ["ruff", "check", str(project_root)],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            print("Linting issues found:")
            print(result.stdout)
            print(result.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: ruff not found. Run 'pip install ruff' first.")
        return 1

def run_format_check(project_root: Path) -> int:
    """Run black formatter check on the project."""
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", str(project_root)],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            print("Formatting issues found:")
            print(result.stdout)
            print(result.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Run 'pip install black' first.")
        return 1

def main() -> int:
    """Main entry point for setup_linting."""
    project_root = Path(__file__).resolve().parent.parent
    
    # Ensure tools are installed
    install_tools()
    
    # Verify/create config files
    verify_config_files(project_root)
    
    # Run checks
    lint_code = run_lint_check(project_root)
    format_code = run_format_check(project_root)
    
    if lint_code == 0 and format_code == 0:
        print("✅ All linting and formatting checks passed.")
        return 0
    else:
        print("⚠️ Some checks failed. Run 'ruff check --fix' and 'black .' to fix.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
