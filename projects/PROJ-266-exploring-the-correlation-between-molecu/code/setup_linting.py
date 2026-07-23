"""
Setup script to verify linting and formatting configuration.

This script checks that flake8 and black are properly configured
and can be executed against the codebase.
"""
import os
import sys
import subprocess
from pathlib import Path

def check_config_files():
    """Verify that linting configuration files exist."""
    project_root = Path(__file__).resolve().parent.parent
    
    required_files = [
        project_root / ".flake8",
        project_root / "pyproject.toml",
        project_root / ".pre-commit-config.yaml",
    ]
    
    missing = [f for f in required_files if not f.exists()]
    
    if missing:
        print(f"ERROR: Missing configuration files: {[f.name for f in missing]}")
        print("Please ensure .flake8, pyproject.toml (with black settings), and .pre-commit-config.yaml exist.")
        return False
    
    print("✓ All linting configuration files found.")
    return True

def run_flake8_check():
    """Run flake8 to verify it works with current configuration."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        print("ERROR: code/ directory not found.")
        return False
    
    try:
        result = subprocess.run(
            ["flake8", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✓ flake8 passed: No style violations found.")
            return True
        else:
            print("⚠ flake8 found style violations:")
            print(result.stdout)
            print(result.stderr)
            # Don't fail the setup if there are just style warnings
            # The goal is to verify flake8 is configured and working
            return True
            
    except subprocess.TimeoutExpired:
        print("ERROR: flake8 check timed out.")
        return False
    except FileNotFoundError:
        print("ERROR: flake8 not installed. Run: pip install flake8")
        return False
    except Exception as e:
        print(f"ERROR: Failed to run flake8: {e}")
        return False

def run_black_check():
    """Run black --check to verify it works with current configuration."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        print("ERROR: code/ directory not found.")
        return False
    
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", str(code_dir)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✓ black passed: All files are properly formatted.")
            return True
        else:
            print("⚠ black found formatting issues:")
            # Show a summary, not the full diff
            lines = result.stdout.split('\n')
            if len(lines) > 10:
                print('\n'.join(lines[:10]))
                print(f"... ({len(lines) - 10} more lines). Run 'black code/' to fix.")
            else:
                print(result.stdout)
            # Don't fail the setup if there are just formatting issues
            # The goal is to verify black is configured and working
            return True
            
    except subprocess.TimeoutExpired:
        print("ERROR: black check timed out.")
        return False
    except FileNotFoundError:
        print("ERROR: black not installed. Run: pip install black")
        return False
    except Exception as e:
        print(f"ERROR: Failed to run black: {e}")
        return False

def main():
    """Main entry point for linting setup verification."""
    print("=" * 60)
    print("Linting and Formatting Configuration Check")
    print("=" * 60)
    
    success = True
    
    # Check configuration files exist
    if not check_config_files():
        success = False
    
    # Check flake8 works
    if not run_flake8_check():
        success = False
    
    # Check black works
    if not run_black_check():
        success = False
    
    print("=" * 60)
    if success:
        print("SUCCESS: Linting and formatting tools are properly configured.")
        print("To fix any issues found:")
        print("  - Run 'black code/' to auto-format files")
        print("  - Run 'flake8 code/' to see detailed style violations")
        print("  - Install pre-commit hooks: 'pre-commit install'")
    else:
        print("FAILURE: Some checks failed. Please review the errors above.")
        sys.exit(1)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())