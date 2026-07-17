import subprocess
import sys
import os
from pathlib import Path

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed."""
    try:
        subprocess.run([tool_name, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_linting(project_root: str) -> int:
    """Run flake8 linting on the project."""
    code_dir = os.path.join(project_root, "code")
    
    if not check_tool_installed("flake8"):
        print("flake8 is not installed. Install it with: pip install flake8")
        return 1
    
    try:
        result = subprocess.run(
            ["flake8", code_dir],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ No linting errors found")
        else:
            print("✗ Linting errors found:")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode
    except Exception as e:
        print(f"Error running flake8: {e}")
        return 1

def run_formatting_check(project_root: str) -> int:
    """Run black formatting check on the project."""
    code_dir = os.path.join(project_root, "code")
    
    if not check_tool_installed("black"):
        print("black is not installed. Install it with: pip install black")
        return 1
    
    try:
        result = subprocess.run(
            ["black", "--check", code_dir],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Code is properly formatted")
        else:
            print("✗ Formatting issues found:")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode
    except Exception as e:
        print(f"Error running black: {e}")
        return 1

def main():
    """Main entry point for linting and formatting setup."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print("Running linting and formatting checks...")
    print("-" * 50)
    
    lint_result = run_linting(project_root)
    print("-" * 50)
    
    format_result = run_formatting_check(project_root)
    print("-" * 50)
    
    if lint_result == 0 and format_result == 0:
        print("✓ All checks passed!")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
