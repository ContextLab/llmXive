"""
T036: Run ruff check --fix and black format on all code/ files.

This script ensures all Python files in the code/ directory are
formatted according to project standards and have no lint errors.

Usage:
    python code/format_and_lint.py
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"✓ {description} completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with return code {e.returncode}")
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        return False

def check_ruff_black_available() -> bool:
    """Check if ruff and black are installed."""
    print("Checking for required tools...")
    
    tools = [
        (["ruff", "--version"], "ruff"),
        (["black", "--version"], "black"),
    ]
    
    all_available = True
    for cmd, tool_name in tools:
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✓ {tool_name} is available")
        except subprocess.CalledProcessError:
            print(f"✗ {tool_name} is NOT available")
            all_available = False
    
    return all_available

def main():
    """Main entry point for T036."""
    print("T036: Running ruff check --fix and black format on all code/ files")
    
    # Check prerequisites
    if not check_ruff_black_available():
        print("\nERROR: Required tools (ruff, black) are not installed.")
        print("Please install them via: pip install ruff black")
        sys.exit(1)
    
    code_dir = Path(__file__).parent
    if not code_dir.exists():
        print(f"ERROR: code/ directory not found at {code_dir}")
        sys.exit(1)
    
    # Find all Python files in code/
    python_files = list(code_dir.rglob("*.py"))
    print(f"\nFound {len(python_files)} Python files in code/")
    
    if not python_files:
        print("WARNING: No Python files found in code/ directory.")
        sys.exit(0)
    
    # Step 1: Run ruff check --fix
    ruff_fix_success = run_command(
        ["ruff", "check", "--fix", "code/"],
        "ruff check --fix"
    )
    
    if not ruff_fix_success:
        print("\nWARNING: ruff check --fix found issues that could not be auto-fixed.")
        print("Please review the output above and fix manually if needed.")
    
    # Step 2: Run black format
    black_format_success = run_command(
        ["black", "code/"],
        "black format"
    )
    
    if not black_format_success:
        print("\nERROR: black formatting failed.")
        sys.exit(1)
    
    # Step 3: Run final ruff check (no --fix) to ensure no lint errors remain
    print("\n" + "="*60)
    print("Final verification: Running ruff check (no auto-fix)")
    print("="*60)
    
    final_check = subprocess.run(
        ["ruff", "check", "code/"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    if final_check.returncode == 0:
        print("✓ Final ruff check passed - no lint errors remain")
    else:
        print("✗ Final ruff check found remaining lint errors:")
        print(final_check.stdout)
        print("Please fix these errors manually.")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("T036 COMPLETED SUCCESSFULLY")
    print("All code/ files are formatted and lint-free")
    print("="*60)

if __name__ == "__main__":
    main()