"""
Linting tool wrapper for Ruff.
Checks code for style and logic errors.
"""
import subprocess
import sys
from pathlib import Path

def run_command(mode: str = "check"):
    """Run Ruff linter on the project code directory."""
    project_root = Path(__file__).resolve().parent.parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"
    config_path = project_root / ".ruff.toml"

    if mode == "check":
        cmd = [
            sys.executable, "-m", "ruff", "check",
            "--config", str(config_path),
            str(code_dir),
            str(tests_dir)
        ]
        print(f"Running: {' '.join(cmd)}")
    elif mode == "fix":
        cmd = [
            sys.executable, "-m", "ruff", "check",
            "--config", str(config_path),
            "--fix",
            str(code_dir),
            str(tests_dir)
        ]
        print(f"Running: {' '.join(cmd)}")
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)

    result = subprocess.run(cmd)
    
    if result.returncode != 0 and mode == "check":
        print("Linting found issues. Run 'python code/tools/lint.py --fix' to attempt automatic fixes.")
        sys.exit(result.returncode)
    
    if mode == "check":
        print("Linting passed.")
    else:
        print("Linting fixes applied.")
    return 0

def main():
    """Entry point for the lint script."""
    import argparse
    parser = argparse.ArgumentParser(description="Run Ruff linter.")
    parser.add_argument("--fix", action="store_true", help="Apply automatic fixes.")
    args = parser.parse_args()

    mode = "fix" if args.fix else "check"
    run_command(mode)

if __name__ == "__main__":
    main()