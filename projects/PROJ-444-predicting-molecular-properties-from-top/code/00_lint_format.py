import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        return False
    except FileNotFoundError:
        print(f"Error: Command not found. Please ensure {' '.join(cmd[:1])} is installed.")
        return False

def main():
    """Main entry point for linting and formatting."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)
    
    print("Starting linting and formatting checks...")
    print("-" * 50)
    
    # Check for ruff installation
    ruff_installed = run_command(
        [sys.executable, "-m", "ruff", "--version"],
        "Checking ruff installation"
    )
    
    if not ruff_installed:
        print("Installing ruff...")
        run_command([sys.executable, "-m", "pip", "install", "ruff"], "Installing ruff")
    
    # Check for black installation
    black_installed = run_command(
        [sys.executable, "-m", "black", "--version"],
        "Checking black installation"
    )
    
    if not black_installed:
        print("Installing black...")
        run_command([sys.executable, "-m", "pip", "install", "black"], "Installing black")
    
    print("-" * 50)
    print("Running linter (ruff)...")
    lint_success = run_command(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        "Linting code directory"
    )
    
    print("-" * 50)
    print("Running formatter (black)...")
    format_success = run_command(
        [sys.executable, "-m", "black", "--check", str(code_dir)],
        "Checking code formatting"
    )
    
    print("-" * 50)
    
    if lint_success and format_success:
        print("✅ All checks passed!")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("To auto-fix formatting issues, run: python code/00_lint_format.py --fix")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Lint and format Python code")
    parser.add_argument("--fix", action="store_true", help="Apply formatting fixes")
    args = parser.parse_args()
    
    if args.fix:
        project_root = Path(__file__).parent.parent
        code_dir = project_root / "code"
        run_command(
            [sys.executable, "-m", "black", str(code_dir)],
            "Applying black formatting fixes"
        )
        run_command(
            [sys.executable, "-m", "ruff", "check", "--fix", str(code_dir)],
            "Applying ruff fixes"
        )
    else:
        main()
