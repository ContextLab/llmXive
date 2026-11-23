"""
Task T002c: Generate lock file for reproducibility.

This script runs `pip freeze` and writes the output to 
`projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.lock`.

It ensures that the exact versions of all installed packages are captured
to satisfy Constitution Principle I (Reproducibility).
"""
import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path("projects/PROJ-312-evaluating-the-impact-of-code-generation")
    lock_file = project_root / "requirements.lock"

    if not project_root.exists():
        raise FileNotFoundError(
            f"Project root directory not found: {project_root}. "
            "Please ensure T001a (directory creation) has been completed."
        )

    print(f"Generating lock file at: {lock_file}")
    
    try:
        # Run pip freeze and capture output
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Write the output to the lock file
        with open(lock_file, "w", encoding="utf-8") as f:
            f.write(result.stdout)
        
        print(f"Successfully wrote {len(result.stdout.splitlines())} packages to {lock_file}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running pip freeze: {e.stderr}")
        raise
    except Exception as e:
        print(f"Unexpected error generating lock file: {e}")
        raise

if __name__ == "__main__":
    main()