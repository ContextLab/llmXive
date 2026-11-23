import subprocess
import sys
import os
from pathlib import Path

def main():
    """
    Run black --check to ensure zero formatting errors across the project codebase.
    Exits with code 0 if all files are correctly formatted, non-zero otherwise.
    """
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)

    print("Running Black formatter check on code/...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--quiet", str(code_dir)],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ All Python files in code/ are correctly formatted.")
            sys.exit(0)
        else:
            print("❌ Black formatting errors detected. Please run 'black code/' to fix.")
            sys.exit(1)
            
    except FileNotFoundError:
        print("Error: 'black' is not installed. Please install it via 'pip install black'.")
        sys.exit(1)
    except Exception as e:
        print(f"Error running black check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()