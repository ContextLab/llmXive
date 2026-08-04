"""
Linting tool wrapper for Ruff.
Runs ruff on the codebase.
"""
import subprocess
import sys
from pathlib import Path

def run_command():
    """Run ruff linter on the project."""
    project_root = Path(__file__).resolve().parents[2]
    code_dir = project_root / "code"
    
    print(f"Running ruff on {code_dir}...")
    
    try:
        # Run ruff check with fix option
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_dir), "--fix"],
            cwd=project_root,
            check=True,
            capture_output=False,
            text=True
        )
        print("Linting completed successfully (no issues found or fixed).")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Linting failed with issues: {e}")
        return 1

def main():
    """Entry point for the lint script."""
    sys.exit(run_command())

if __name__ == "__main__":
    main()