import subprocess
import sys
from pathlib import Path
import os

def check_tool_availability(tool_name: str) -> bool:
    """Check if a tool is available in the system PATH."""
    try:
        subprocess.run([tool_name, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_lint_check() -> bool:
    """Run ruff lint check on the code directory."""
    if not check_tool_availability("ruff"):
        print("ERROR: ruff is not installed. Please install it via pip install ruff.")
        return False
    
    code_dir = Path(__file__).parent.parent
    result = subprocess.run(
        ["ruff", "check", str(code_dir / "code")],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("Ruff linting failed:")
        print(result.stdout)
        print(result.stderr)
        return False
    
    print("Ruff linting passed.")
    return True

def run_format_check() -> bool:
    """Run black format check on the code directory."""
    if not check_tool_availability("black"):
        print("ERROR: black is not installed. Please install it via pip install black.")
        return False
    
    code_dir = Path(__file__).parent.parent
    result = subprocess.run(
        ["black", "--check", str(code_dir / "code")],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("Black formatting check failed:")
        print(result.stdout)
        print(result.stderr)
        return False
    
    print("Black formatting check passed.")
    return True

def setup_pre_commit_hooks() -> bool:
    """Setup pre-commit hooks for linting and formatting."""
    code_dir = Path(__file__).parent.parent
    pre_commit_path = code_dir / ".pre-commit-config.yaml"
    
    if not pre_commit_path.exists():
        config_content = """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
- id: ruff
  args: [--fix]
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
- id: black
"""
        with open(pre_commit_path, "w") as f:
            f.write(config_content)
        print(f"Created {pre_commit_path}")
    
    # Install pre-commit if not available
    if not check_tool_availability("pre-commit"):
        print("Installing pre-commit...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pre-commit"], check=True)
    
    # Initialize git hooks if in a git repo
    if (code_dir / ".git").exists():
        subprocess.run(["pre-commit", "install"], cwd=code_dir, check=True)
        print("Pre-commit hooks installed.")
    else:
        print("Not in a git repository. Skipping pre-commit installation.")
    
    return True

def main():
    """Main entry point for linting setup."""
    print("=== Linting and Formatting Setup ===")
    
    # Check availability
    if not check_tool_availability("ruff"):
        print("Installing ruff...")
        subprocess.run([sys.executable, "-m", "pip", "install", "ruff"], check=True)
    
    if not check_tool_availability("black"):
        print("Installing black...")
        subprocess.run([sys.executable, "-m", "pip", "install", "black"], check=True)
    
    # Run checks
    lint_ok = run_lint_check()
    format_ok = run_format_check()
    
    if lint_ok and format_ok:
        print("\nAll checks passed!")
    else:
        print("\nSome checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()