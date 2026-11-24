"""
Wrapper script to invoke the project's plan scope verification.

The test suite expects the script at `projects/code/verify_plan_scope.py`.
This wrapper adjusts the Python path to import the actual implementation
located in the project-specific `code/` directory and forwards execution
to it.
"""
import sys
from pathlib import Path

# Determine the root of the specific project (the sibling folder under `projects/`)
# This file resides in `projects/code/`. The project directory is two levels up:
#   projects/
#     code/
#     PROJ-203-predicting-phase-transitions-in-amorphou/
project_root = Path(__file__).resolve().parents[1] / "PROJ-203-predicting-phase-transitions-in-amorphou"
code_dir = project_root / "code"

# Add the project's code directory to sys.path so we can import its modules
sys.path.insert(0, str(code_dir))

# Import the actual verification script's main function
try:
    from verify_plan_scope import main as verify_main
except ImportError as e:
    print(f"Failed to import verify_plan_scope from project code: {e}", file=sys.stderr)
    sys.exit(1)

# Execute the verification logic
if __name__ == "__main__":
    verify_main()