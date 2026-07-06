"""
Utility script to run strict linting checks without auto-fixing.
Used in CI/CD pipelines.
"""
import subprocess
import sys
import os

def run_command(cmd: list[str]) -> int:
    """Run a shell command and return its exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    return result.returncode

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)

    # Check if dependencies are installed
    try:
        import ruff
        import black
    except ImportError:
        print("Error: Linting dependencies not installed.")
        return 1

    # Run Ruff (Strict Lint)
    print("\n--- Running Ruff Linter (Strict) ---")
    ret = run_command(["ruff", "check", "code/", "tests/"])
    if ret != 0:
        print("❌ Linting errors found.")
        return ret

    # Run Black (Check only)
    print("\n--- Running Black Format Check ---")
    ret = run_command(["black", "code/", "tests/", "--check"])
    if ret != 0:
        print("❌ Formatting errors found.")
        return ret

    print("\n✅ All linting and formatting checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())