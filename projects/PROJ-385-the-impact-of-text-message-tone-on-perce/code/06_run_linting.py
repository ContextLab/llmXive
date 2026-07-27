import subprocess
import sys
from pathlib import Path

def run_command(cmd: list, cwd: Path) -> bool:
    """
    Runs a shell command and returns True if it succeeds (exit code 0), False otherwise.
    Prints output to stdout/stderr in real-time.
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False
        )
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        return False

def main():
    """
    Entry point for T034: Run linting and formatting checks on code/
    
    This script runs ruff and black checks against the code/ directory.
    It exits with code 0 if all checks pass (0 errors), and non-zero otherwise.
    """
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Running linting and formatting checks on {code_dir}...")
    print("=" * 60)

    # Check Ruff (linting)
    print("\n[1/2] Running Ruff checks...")
    ruff_cmd = ["python", "-m", "ruff", "check", str(code_dir)]
    ruff_success = run_command(ruff_cmd, project_root)

    # Check Black (formatting)
    print("\n[2/2] Running Black checks...")
    black_cmd = ["python", "-m", "black", "--check", str(code_dir)]
    black_success = run_command(black_cmd, project_root)

    print("=" * 60)

    if ruff_success and black_success:
        print("✅ All linting and formatting checks passed (0 errors).")
        sys.exit(0)
    else:
        print("❌ Linting or formatting checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
