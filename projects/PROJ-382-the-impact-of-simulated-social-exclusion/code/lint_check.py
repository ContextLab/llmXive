"""
Verification script for linting compliance.

Runs flake8 and black --check to validate code quality standards.
Exits with non-zero status if any violations are found.
"""
import subprocess
import sys
from pathlib import Path


def run_command(command: list, description: str) -> bool:
    """
    Run a command and return True if it succeeds.
    
    Args:
        command: List of command arguments.
        description: Human-readable description for logging.
        
    Returns:
        True if command exits with code 0, False otherwise.
    """
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"\n✓ {description} passed successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} failed with exit code {e.returncode}.\n")
        if e.stderr:
            print(f"Stderr: {e.stderr}\n")
        return False
    except FileNotFoundError:
        print(f"\n✗ {description} failed: Command not found.\n")
        print("Please ensure the required tools are installed:")
        print("  pip install flake8 black\n")
        return False


def main():
    """Run all linting checks."""
    project_root = Path(__file__).parent.parent
    osf_dir = project_root / 'projects' / 'PROJ-382-the-impact-of-simulated-social-exclusion'
    
    # Change to project root if the script is in code/
    if (project_root / 'code').exists():
        osf_dir = project_root
    
    code_dir = osf_dir / 'code'
    
    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        print("Please ensure the project structure is correct.")
        sys.exit(1)
    
    print(f"Running linting checks for project: {osf_dir}")
    print(f"Code directory: {code_dir}")
    
    all_passed = True
    
    # Run flake8
    flake8_cmd = [
        sys.executable, "-m", "flake8",
        str(code_dir),
        "--config=.flake8"
    ]
    if not run_command(flake8_cmd, "flake8"):
        all_passed = False
    
    # Run black --check
    black_cmd = [
        sys.executable, "-m", "black",
        "--check",
        "--config=pyproject.toml",
        str(code_dir)
    ]
    if not run_command(black_cmd, "black --check"):
        all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✓ All linting checks passed!")
        sys.exit(0)
    else:
        print("✗ Some linting checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
