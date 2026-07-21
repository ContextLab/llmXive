import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, cwd: Path = None) -> int:
    """
    Execute a shell command and return the exit code.
    Raises RuntimeError if the command fails.
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}. Ensure tools are installed.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        return 1

def main():
    """
    Main entry point for linting and formatting.
    Runs ruff check (linting) and black (formatting).
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    # Check if tools are installed
    try:
        subprocess.run(["ruff", "--version"], stdout=subprocess.DEVNULL, check=True)
        subprocess.run(["black", "--version"], stdout=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        print("Error: 'ruff' or 'black' not found. Please install them.", file=sys.stderr)
        print("Run: pip install ruff black", file=sys.stderr)
        sys.exit(1)

    # 1. Run Linting (Ruff)
    print("Running Ruff linting...")
    lint_cmd = ["ruff", "check", str(code_dir), str(tests_dir)]
    lint_exit_code = run_command(lint_cmd, cwd=project_root)

    # 2. Run Formatting (Black)
    # Note: We run black in check mode first. If it fails, we can optionally run it to fix.
    # For CI/strict mode, we just check. For local dev, we might fix.
    # Here we implement a strict check-first approach, then fix if requested or if check fails.
    print("Running Black formatting check...")
    format_check_cmd = ["black", "--check", str(code_dir), str(tests_dir)]
    format_exit_code = run_command(format_check_cmd, cwd=project_root)

    if format_exit_code != 0:
        print("Formatting issues detected. Attempting to fix...")
        fix_cmd = ["black", str(code_dir), str(tests_dir)]
        fix_exit_code = run_command(fix_cmd, cwd=project_root)
        if fix_exit_code != 0:
            print("Failed to auto-fix formatting issues.", file=sys.stderr)
            sys.exit(fix_exit_code)

    # Exit with the highest error code (linting usually more critical for CI)
    if lint_exit_code != 0:
        print("Linting errors found.", file=sys.stderr)
        sys.exit(lint_exit_code)

    print("All linting and formatting checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
