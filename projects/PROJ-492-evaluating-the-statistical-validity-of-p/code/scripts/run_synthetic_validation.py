"""
Script to run synthetic validation evaluation.
Executes the evaluation task and reports results.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.src.audit.evaluation import main as run_evaluation

def main():
    """Main entry point."""
    print("Running synthetic validation evaluation...")
    exit_code = run_evaluation()
    
    if exit_code == 0:
        print("✓ Evaluation completed successfully")
    else:
        print("✗ Evaluation failed")
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main())