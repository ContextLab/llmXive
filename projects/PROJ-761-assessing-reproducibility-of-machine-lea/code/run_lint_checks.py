import subprocess
import sys
import os

def run_command(cmd: list[str]) -> int:
    """Run a command and return its exit code."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        return e.returncode

def main() -> None:
    """Run initial linting and formatting checks on the project structure."""
    print("=== Linting and Formatting Validation ===")
    print("Running checks on empty project structure to verify configuration...")
    
    # Ensure we are in the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    # Run ruff check
    ruff_check_code = run_command(["ruff", "check", "code/", "tests/"])
    
    # Run ruff format check (dry-run to verify config)
    ruff_format_code = run_command(["ruff", "format", "--check", "code/", "tests/"])
    
    # Run black check (dry-run)
    black_code = run_command(["black", "--check", "code/", "tests/"])
    
    print("\n=== Summary ===")
    if ruff_check_code == 0 and ruff_format_code == 0 and black_code == 0:
        print("All linting and formatting checks passed!")
        sys.exit(0)
    else:
        print("Some checks failed. Review the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
