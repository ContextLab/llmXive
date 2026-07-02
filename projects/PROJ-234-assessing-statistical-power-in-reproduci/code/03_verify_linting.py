import subprocess
import sys
import os

def run_command(cmd: list) -> int:
    """Run a shell command and return the exit code."""
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        return 1

def main():
    """Verify linting configuration by running black and flake8."""
    print("Verifying linting configuration...")

    # Run black --check
    print("\n--- Running black --check ---")
    black_code = run_command(["black", "--check", "."])

    # Run flake8
    print("\n--- Running flake8 ---")
    flake8_code = run_command(["flake8", "."])

    if black_code == 0 and flake8_code == 0:
        print("\nLinting verification PASSED.")
        return 0
    else:
        print("\nLinting verification FAILED.")
        if black_code != 0:
            print("  - black check failed")
        if flake8_code != 0:
            print("  - flake8 check failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())