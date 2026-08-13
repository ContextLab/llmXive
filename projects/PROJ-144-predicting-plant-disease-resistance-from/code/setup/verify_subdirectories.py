"""
Task T001c (Helper): Verify that sub-directories exist and are writable.
This script generates the verification artifact for T001c but is called here
to satisfy the dependency of T001b's verification step if needed, or run standalone.

Output: Prints directory structure to stdout (can be redirected to state/directory_structure.txt)
"""
import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def check_directory_writable(dir_path: Path) -> bool:
    """Check if a directory exists and is writable."""
    if not dir_path.exists():
        print(f"FAIL: Directory does not exist: {dir_path}")
        return False
    if not os.access(dir_path, os.W_OK):
        print(f"FAIL: Directory is not writable: {dir_path}")
        return False
    return True

def run_ls_recursive():
    """Run 'ls -R' on the project root to verify structure."""
    try:
        result = subprocess.run(
            ["ls", "-R", str(PROJECT_ROOT)],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running ls -R: {e}")
        print(f"stderr: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: 'ls' command not found. Attempting Python fallback.")
        # Fallback if 'ls' is not available (e.g., Windows without git-bash)
        for root, dirs, files in os.walk(PROJECT_ROOT):
            level = root.replace(str(PROJECT_ROOT), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f'{subindent}{file}')
        return "Fallback listing completed."

def main():
    """Verify directories created in T001a/T001b."""
    dirs_to_check = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "intermediate",
        PROJECT_ROOT / "results" / "plots",
    ]

    all_ok = True
    for d in dirs_to_check:
        if not check_directory_writable(d):
            all_ok = False

    if all_ok:
        print("\n--- Directory Structure Verification (ls -R) ---")
        run_ls_recursive()
        print("\nT001c: All sub-directories verified as existing and writable.")
        sys.exit(0)
    else:
        print("\nT001c: Verification FAILED. Some directories missing or not writable.")
        sys.exit(1)

if __name__ == "__main__":
    main()