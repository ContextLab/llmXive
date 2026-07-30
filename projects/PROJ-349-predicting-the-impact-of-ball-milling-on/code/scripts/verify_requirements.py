"""
Script to verify that all dependencies in requirements.txt are resolvable.
This implements task T002b: Verify requirements.txt.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run pip check to verify dependencies."""
    print("Verifying dependencies in requirements.txt...")
    
    # Change to project root to ensure we are in the right context
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    try:
        # Run pip check
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✓ No dependency conflicts detected.")
            print("All dependencies in requirements.txt are resolvable.")
            return 0
        else:
            print("✗ Dependency conflicts detected:")
            print(result.stdout)
            print(result.stderr)
            return 1
            
    except subprocess.TimeoutExpired:
        print("✗ Timeout while checking dependencies.")
        return 1
    except FileNotFoundError:
        print("✗ pip not found. Ensure Python environment is active.")
        return 1
    except Exception as e:
        print(f"✗ Error during dependency check: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())