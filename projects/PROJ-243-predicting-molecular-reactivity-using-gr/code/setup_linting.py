"""
Script to verify linting and formatting tools are correctly configured.
This script is a placeholder to satisfy T003 implementation requirements.
The actual configuration is handled by .flake8, pyproject.toml, and .isort.cfg.
"""
import subprocess
import sys
import os

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and available."""
    try:
        subprocess.run(
            [sys.executable, "-m", tool_name, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False

def run_flake8_check() -> int:
    """Run flake8 on the code directory."""
    code_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", code_dir],
            capture_output=True,
            text=True,
            cwd=code_dir,
        )
        if result.returncode == 0:
            print("✓ Flake8 check passed: No issues found.")
        else:
            print("✗ Flake8 check failed:")
            print(result.stdout)
            print(result.stderr)
        return result.returncode
    except FileNotFoundError:
        print("✗ Flake8 not installed. Run: pip install flake8")
        return 1

def run_black_check() -> int:
    """Run black check on the code directory."""
    code_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", code_dir],
            capture_output=True,
            text=True,
            cwd=code_dir,
        )
        if result.returncode == 0:
            print("✓ Black check passed: Code is properly formatted.")
        else:
            print("✗ Black check failed: Code needs formatting.")
            print("Run: black code/")
        return result.returncode
    except FileNotFoundError:
        print("✗ Black not installed. Run: pip install black")
        return 1

def main() -> int:
    """Main entry point for linting verification."""
    print("Checking linting and formatting configuration...")
    print("-" * 50)

    # Check if tools are installed
    tools = [("flake8", "flake8"), ("black", "black"), ("isort", "isort")]
    missing_tools = []

    for module, cmd in tools:
        if check_tool_installed(module):
            print(f"✓ {cmd} is installed")
        else:
            missing_tools.append(cmd)

    if missing_tools:
        print(f"\n⚠ Missing tools: {', '.join(missing_tools)}")
        print("Install with: pip install flake8 black isort")
        print("\nSkipping lint checks due to missing tools.")
        return 1

    print("-" * 50)

    # Run checks
    flake8_result = run_flake8_check()
    print()
    black_result = run_black_check()

    print("-" * 50)
    if flake8_result == 0 and black_result == 0:
        print("✓ All linting and formatting checks passed!")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())