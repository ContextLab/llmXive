"""
Formatting tool wrapper for Black.
Runs black on the codebase.
"""
import subprocess
import sys
from pathlib import Path

def run_command():
    """Run black formatter on the project."""
    project_root = Path(__file__).resolve().parents[2]
    code_dir = project_root / "code"
    
    print(f"Running black on {code_dir}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", str(code_dir)],
            cwd=project_root,
            check=True,
            capture_output=False,
            text=True
        )
        print("Formatting completed successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Formatting failed: {e}")
        return 1

def main():
    """Entry point for the format script."""
    sys.exit(run_command())

if __name__ == "__main__":
    main()
