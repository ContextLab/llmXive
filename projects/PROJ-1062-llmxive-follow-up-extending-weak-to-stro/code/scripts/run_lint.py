"""
Script to run Ruff linter on the project codebase.
"""
import subprocess
import sys
import os

def main():
    """Run ruff linter on the code directory."""
    print("Running Ruff linter...")
    try:
        # Run ruff check on the code directory
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "code/", "tests/"],
            check=True,
            capture_output=False,
            text=True
        )
        if result.returncode == 0:
            print("Linting passed successfully.")
        else:
            print(f"Linting found issues (exit code {result.returncode}).")
            # Do not exit with error code here to allow CI to handle the specific failure logic if needed,
            # but typically we want to fail the build on lint errors.
            sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        # Ruff prints errors to stderr/stdout, so we just propagate the exit code.
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("Error: ruff is not installed. Please install it via 'pip install ruff'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
