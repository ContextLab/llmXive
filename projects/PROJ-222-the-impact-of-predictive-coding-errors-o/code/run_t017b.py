"""
Runner script for T017b: Save Markov Artifacts.

This script executes the T017b task to generate transition probability tables
and Markov model state artifacts.
"""
import sys
from pathlib import Path

# Ensure the code directory is in the path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from save_markov_artifacts import run_t017b
from config import set_seed

def main():
    """Main entry point for the T017b runner."""
    print("Executing T017b: Save Markov Artifacts...")
    
    # Set seed for reproducibility (though this task is deterministic on data)
    set_seed(42)
    
    result = run_t017b(seed=42)
    
    if result['status'] == 'success':
        print(f"Success! Artifacts saved to:")
        for f in result['files_saved']:
            print(f"  - {f}")
        print(f"Processed {result['participants_processed']} participants.")
        return 0
    else:
        print(f"Failed: {result.get('reason', 'Unknown error')}")
        return 1

if __name__ == "__main__":
    sys.exit(main())