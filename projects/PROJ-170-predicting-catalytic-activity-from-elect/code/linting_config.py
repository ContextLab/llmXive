"""
Linting and formatting configuration management for the project.
Implements T002: Configure linting (ruff/flake8) and formatting (black) tools.
"""
import os
import sys
import subprocess
from pathlib import Path
from config import get_project_root

def ensure_linting_config():
    """
    Verify that .ruff.toml and pyproject.toml (with black config) exist in the project root.
    Raises FileNotFoundError if configuration files are missing.
    """
    project_root = get_project_root()
    ruff_config = project_root / ".ruff.toml"
    pyproject_config = project_root / "pyproject.toml"

    if not ruff_config.exists():
        raise FileNotFoundError(f"Ruff configuration file not found: {ruff_config}")
    
    if not pyproject_config.exists():
        raise FileNotFoundError(f"Pyproject configuration file not found: {pyproject_config}")
    
    # Verify black section exists in pyproject.toml
    with open(pyproject_config, 'r', encoding='utf-8') as f:
        content = f.read()
        if '[tool.black]' not in content:
            raise ValueError("Black configuration section missing from pyproject.toml")
    
    # Verify ruff section exists in pyproject.toml or .ruff.toml handles it
    if '[tool.ruff]' not in content and not ruff_config.exists():
        # If not in pyproject, .ruff.toml must exist (already checked above)
        pass

def run_black_check():
    """
    Run black --check on the project.
    Returns True if all files are formatted correctly, False otherwise.
    """
    project_root = get_project_root()
    try:
        result = subprocess.run(
            ["black", "--check", "--config", str(project_root / "pyproject.toml"), "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print("✓ All files are formatted correctly (Black check passed)")
            return True
        else:
            print("✗ Black check failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("✗ Black check timed out")
        return False
    except FileNotFoundError:
        print("✗ Black not installed. Run: pip install black")
        return False

def run_ruff_check():
    """
    Run ruff check with the project configuration.
    Returns True if no linting errors found, False otherwise.
    """
    project_root = get_project_root()
    ruff_config = project_root / ".ruff.toml"
    
    try:
        result = subprocess.run(
            ["ruff", "check", "--config", str(ruff_config), "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print("✓ All files passed linting (Ruff check passed)")
            return True
        else:
            print("✗ Ruff check failed:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("✗ Ruff check timed out")
        return False
    except FileNotFoundError:
        print("✗ Ruff not installed. Run: pip install ruff")
        return False

def run_black_format():
    """
    Run black to format all files in the project.
    """
    project_root = get_project_root()
    try:
        result = subprocess.run(
            ["black", "--config", str(project_root / "pyproject.toml"), "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print("✓ Files formatted successfully")
            return True
        else:
            print("✗ Black formatting failed:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("✗ Black formatting timed out")
        return False
    except FileNotFoundError:
        print("✗ Black not installed. Run: pip install black")
        return False

def run_ruff_fix():
    """
    Run ruff to automatically fix linting issues.
    """
    project_root = get_project_root()
    ruff_config = project_root / ".ruff.toml"
    
    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", "--config", str(ruff_config), "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print("✓ Linting issues fixed successfully")
            return True
        else:
            print("✗ Ruff fix failed (some issues may not be auto-fixable):")
            print(result.stdout)
            return False
    except subprocess.TimeoutExpired:
        print("✗ Ruff fix timed out")
        return False
    except FileNotFoundError:
        print("✗ Ruff not installed. Run: pip install ruff")
        return False

def main():
    """
    Main entry point for linting configuration tasks.
    Performs verification as required by T002.
    """
    print("=== T002: Configuring Linting and Formatting Tools ===")
    
    # Ensure configuration files exist
    try:
        ensure_linting_config()
        print("✓ Configuration files verified")
    except (FileNotFoundError, ValueError) as e:
        print(f"✗ Configuration verification failed: {e}")
        sys.exit(1)
    
    # Run checks
    black_ok = run_black_check()
    ruff_ok = run_ruff_check()
    
    if black_ok and ruff_ok:
        print("\n=== T002 Verification: PASSED ===")
        print("All linting and formatting checks passed.")
        sys.exit(0)
    else:
        print("\n=== T002 Verification: FAILED ===")
        if not black_ok:
            print("- Black check failed. Run 'python code/linting_config.py format' to fix.")
        if not ruff_ok:
            print("- Ruff check failed. Run 'python code/linting_config.py fix' to fix.")
        sys.exit(1)

if __name__ == "__main__":
    main()
