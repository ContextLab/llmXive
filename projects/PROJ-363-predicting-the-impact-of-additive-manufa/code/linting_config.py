import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return None

def check_linting(root_dir):
    """Run ruff check on the project."""
    cmd = "ruff check ."
    result = run_command(cmd, cwd=root_dir)
    if result is None:
        print("Linting check failed or ruff is not installed.")
        return False
    if result.returncode == 0:
        print("Linting check passed.")
        return True
    else:
        print("Linting issues found:")
        print(result.stdout)
        return False

def check_formatting(root_dir):
    """Run black --check on the project."""
    cmd = "black --check ."
    result = run_command(cmd, cwd=root_dir)
    if result is None:
        print("Formatting check failed or black is not installed.")
        return False
    if result.returncode == 0:
        print("Formatting check passed.")
        return True
    else:
        print("Formatting issues found.")
        return False

def fix_linting(root_dir):
    """Run ruff check --fix on the project."""
    cmd = "ruff check --fix ."
    result = run_command(cmd, cwd=root_dir)
    if result is None:
        print("Auto-fixing linting failed or ruff is not installed.")
        return False
    if result.returncode == 0:
        print("Linting auto-fix completed successfully.")
        return True
    else:
        print("Linting auto-fix encountered issues.")
        print(result.stdout)
        return False

def fix_formatting(root_dir):
    """Run black on the project to format code."""
    cmd = "black ."
    result = run_command(cmd, cwd=root_dir)
    if result is None:
        print("Auto-formatting failed or black is not installed.")
        return False
    if result.returncode == 0:
        print("Code formatted successfully.")
        return True
    else:
        print("Formatting encountered issues.")
        print(result.stdout)
        return False

def main():
    """Main entry point for linting and formatting tools."""
    root_dir = Path(__file__).resolve().parent.parent
    print(f"Running tools for project at: {root_dir}")

    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "check":
            lint_ok = check_linting(root_dir)
            fmt_ok = check_formatting(root_dir)
            if lint_ok and fmt_ok:
                print("All checks passed.")
                sys.exit(0)
            else:
                print("Some checks failed.")
                sys.exit(1)
        elif action == "fix":
            fix_linting(root_dir)
            fix_formatting(root_dir)
            print("Fix commands executed.")
            sys.exit(0)
        else:
            print(f"Unknown action: {action}")
            sys.exit(1)
    else:
        print("Usage: python linting_config.py [check|fix]")
        sys.exit(1)

if __name__ == "__main__":
    main()
