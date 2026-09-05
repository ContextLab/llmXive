"""
Runner script for T084: Final Review of Spec and Plan.
Invokes src/evaluation/verify_specs.py with standard arguments.
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    script_path = project_root / "src" / "evaluation" / "verify_specs.py"
    
    if not script_path.exists():
        print(f"Error: Script not found at {script_path}")
        sys.exit(1)

    cmd = [sys.executable, str(script_path)]
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=project_root)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
