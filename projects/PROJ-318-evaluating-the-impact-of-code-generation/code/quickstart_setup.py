"""
Quickstart script to verify T001a and T001b completion.
This script creates the project structure, adds .gitkeep files,
and provides verification output as required by the tasks.
"""
import os
import sys
from pathlib import Path
import subprocess

def run_command(cmd, description):
    """Run a shell command and print its output."""
    print(f"\n--- {description} ---")
    print(f"Command: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    print(f"Exit code: {result.returncode}")
    return result.returncode

def main():
    """Main entry point for quickstart verification."""
    print("=== T001a & T001b Verification Quickstart ===")
    print("This script creates the project structure and verifies it.")
    
    # Create directories
    mkdir_cmd = "mkdir -p code code/utils data/raw/repos data/processed tests/unit tests/integration state logs"
    ret = run_command(mkdir_cmd, "Creating directory structure (T001a)")
    if ret != 0:
        print("ERROR: Failed to create directories")
        return 1
    
    # Verify directories exist
    verify_cmd = "test -d code && test -d code/utils && test -d data/raw/repos && test -d data/processed && test -d tests/unit && test -d tests/integration && test -d state && test -d logs"
    ret = run_command(verify_cmd, "Verifying directory existence (T001a)")
    if ret != 0:
        print("ERROR: Directory verification failed")
        return 1
    
    print("\n✓ T001a PASSED: All directories created and verified")
    
    # Create .gitkeep files
    print("\n--- Creating .gitkeep files (T001b) ---")
    dirs = ["code", "code/utils", "data/raw/repos", "data/processed", "tests/unit", "tests/integration", "state", "logs"]
    for d in dirs:
        gitkeep_path = Path(d) / ".gitkeep"
        gitkeep_path.touch(exist_ok=True)
        print(f"Created: {gitkeep_path}")
    
    # Verify .gitkeep count
    find_cmd = "find code data tests state logs -name .gitkeep | wc -l"
    ret = run_command(find_cmd, "Verifying .gitkeep count (T001b)")
    if ret != 0:
        print("ERROR: .gitkeep verification failed")
        return 1
    
    # Check count is 8
    output = subprocess.run(find_cmd, shell=True, capture_output=True, text=True).stdout.strip()
    if output == "8":
        print("\n✓ T001b PASSED: Exactly 8 .gitkeep files found")
    else:
        print(f"\n✗ T001b FAILED: Expected 8 .gitkeep files, found {output}")
        return 1
    
    print("\n=== All Setup Tasks (T001a, T001b) Completed Successfully ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())