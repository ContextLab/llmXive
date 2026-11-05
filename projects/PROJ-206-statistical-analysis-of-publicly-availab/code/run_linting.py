import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    return result.returncode

def main():
    print("--- Starting Linting and Formatting Verification ---")
    
    # 1. Run Ruff
    ruff_code = run_command(["ruff", "check", "."])
    
    # 2. Run Black check
    black_code = run_command(["black", "--check", "."])
    
    # 3. Run Flake8
    flake_code = run_command(["flake8", "."])
    
    print("\n--- Results ---")
    print(f"Ruff: {'PASS' if ruff_code == 0 else 'FAIL'}")
    print(f"Black: {'PASS' if black_code == 0 else 'FAIL'}")
    print(f"Flake8: {'PASS' if flake_code == 0 else 'FAIL'}")
    
    if ruff_code == 0 and black_code == 0 and flake_code == 0:
        print("\nAll linting and formatting checks passed successfully.")
        sys.exit(0)
    else:
        print("\nOne or more linting/formatting checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()