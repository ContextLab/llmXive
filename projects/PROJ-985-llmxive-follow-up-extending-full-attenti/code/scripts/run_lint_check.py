import subprocess
import sys
import os

def run_command(cmd: list, description: str) -> bool:
    """Run a command and return True if it succeeds."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error in {description}:")
        print(e.stdout)
        return False
    except FileNotFoundError:
        print(f"Error: Command not found. Please ensure {' '.join(cmd[:2])} is installed.")
        return False

def main():
    """Run linting and formatting checks."""
    print("=" * 60)
    print("Running Linting and Formatting Checks")
    print("=" * 60)

    # Change to project root (assuming script is in code/scripts/)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    os.chdir(project_root)
    print(f"Working directory: {project_root}")

    # Run ruff check
    ruff_success = run_command(
        ["python", "-m", "ruff", "check", ".", "--exit-zero"],
        "Ruff Lint Check"
    )

    # Run black check
    black_success = run_command(
        ["python", "-m", "black", "--check", "."],
        "Black Format Check"
    )

    print("=" * 60)
    if ruff_success and black_success:
        print("SUCCESS: All linting and formatting checks passed.")
        sys.exit(0)
    else:
        print("FAILURE: Some checks failed.")
        if not ruff_success:
            print("  - Ruff check failed")
        if not black_success:
            print("  - Black check failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
