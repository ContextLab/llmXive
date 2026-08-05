"""
Script to verify that linting and formatting tools are configured and functional.
This implements T003 verification.
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(__file__).parent.parent,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", f"Command not found: {cmd[0]}"

def main() -> int:
    """Check ruff and black availability and configuration."""
    print("Checking linting and formatting tools...")

    # Check ruff
    print("\n1. Checking Ruff...")
    code, stdout, stderr = run_command(["ruff", "--version"])
    if code != 0:
        print(f"   ERROR: Ruff not found or failed. stderr: {stderr}")
        return 1
    print(f"   Found: {stdout.strip()}")

    # Run ruff check
    print("   Running ruff check...")
    code, stdout, stderr = run_command(["ruff", "check", "code/", "tests/"])
    if code == 0:
        print("   OK: No linting errors found.")
    else:
        print(f"   WARN: Linting issues found (this is expected if code is not perfect):")
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)

    # Check black
    print("\n2. Checking Black...")
    code, stdout, stderr = run_command(["black", "--version"])
    if code != 0:
        print(f"   ERROR: Black not found or failed. stderr: {stderr}")
        return 1
    print(f"   Found: {stdout.strip()}")

    # Run black check
    print("   Running black check (dry run)...")
    code, stdout, stderr = run_command(["black", "--check", "code/", "tests/"])
    if code == 0:
        print("   OK: Code is formatted correctly.")
    else:
        print(f"   WARN: Formatting issues found. Run 'black code/ tests/' to fix.")
        if stdout:
            print(stdout)
        if stderr:
            print(stderr)

    print("\nLinting and formatting tools are configured and functional.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
