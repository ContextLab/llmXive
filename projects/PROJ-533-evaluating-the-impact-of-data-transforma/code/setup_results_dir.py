"""
Setup script to create the results/ directory.
Implements T001c: Create `results/` directory using `mkdir -p results` and verify existence.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the results directory and verify its existence."""
    project_root = Path(__file__).parent.parent
    results_dir = project_root / "results"

    try:
        # Create directory if it doesn't exist (equivalent to mkdir -p)
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify existence
        if not results_dir.is_dir():
            raise RuntimeError(f"Failed to create results directory: {results_dir}")
        
        # Verify we can write to it (basic permission check)
        test_file = results_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        
        print(f"Successfully created and verified results directory at: {results_dir}")
        return 0
        
    except Exception as e:
        print(f"Error creating results directory: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())