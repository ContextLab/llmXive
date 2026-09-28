"""
Format check script to validate C++ and Python code style.
Uses clang-format for C++ and black/flake8 for Python.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"Checking: {description}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR in {description}:")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False

def main():
    """Main entry point for format checking."""
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)

    errors = []

    # Check C++ files with clang-format
    cpp_files = list(project_root.rglob("*.cpp")) + list(project_root.rglob("*.hpp"))
    if cpp_files:
        print(f"Found {len(cpp_files)} C++ files to check")
        for cpp_file in cpp_files:
            if not run_command(
                ["clang-format", "--dry-run", "--Werror", str(cpp_file)],
                f"clang-format: {cpp_file}"
            ):
                errors.append(f"clang-format failed for {cpp_file}")
    else:
        print("No C++ files found")

    # Check Python files with black
    python_files = list(project_root.rglob("*.py"))
    # Exclude data, state, figures directories
    python_files = [f for f in python_files if "data" not in f.parts and "state" not in f.parts and "figures" not in f.parts]
    
    if python_files:
        print(f"Found {len(python_files)} Python files to check")
        if not run_command(
            ["black", "--check", "--diff"] + [str(f) for f in python_files],
            "black: Python code style"
        ):
            errors.append("black check failed")
    else:
        print("No Python files found")

    # Check Python files with flake8
    if python_files:
        if not run_command(
            ["flake8"] + [str(f) for f in python_files],
            "flake8: Python linting"
        ):
            errors.append("flake8 check failed")
    else:
        print("No Python files found for flake8")

    if errors:
        print(f"\nFormat check failed with {len(errors)} errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\nAll format checks passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
