"""
Script to run linting and formatting checks for the project.
This script acts as a unified entry point for CI/CD or manual verification.
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Success: {description}\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed: {description}")
        if e.stdout:
            print(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            print(f"STDERR:\n{e.stderr}")
        print("-" * 40)
        return False

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code_dir = os.path.join(base_dir, "code")
    analysis_dir = os.path.join(code_dir, "analysis")
    benchmark_dir = os.path.join(code_dir, "benchmark")

    # Change to code directory for relative config resolution
    os.chdir(code_dir)

    checks_passed = True

    # 1. Check Python formatting (Black)
    checks_passed &= run_command(
        ["black", "--check", "--config", ".black", "."],
        "Python Black Formatting Check"
    )

    # 2. Check Python linting (Flake8)
    checks_passed &= run_command(
        ["flake8", "--config", ".flake8", "."],
        "Python Flake8 Linting Check"
    )

    # 3. Check C++ formatting (clang-format)
    # Find all .cpp and .hpp files
    cpp_files = []
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith((".cpp", ".hpp", ".h")):
                cpp_files.append(os.path.join(root, file))

    if cpp_files:
        checks_passed &= run_command(
            ["clang-format", "--dry-run", "--Werror", "-style=file"] + cpp_files,
            "C++ clang-format Check"
        )
    else:
        print("No C++ files found to check.")

    if checks_passed:
        print("\nAll checks passed successfully!")
        sys.exit(0)
    else:
        print("\nSome checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()