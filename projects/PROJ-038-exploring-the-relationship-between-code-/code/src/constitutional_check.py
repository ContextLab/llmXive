"""
Constitutional Compliance Check for llmXive Pipeline.

This module verifies the existence of the required amendment artifact
before allowing the pipeline to proceed.
"""
import os
import sys
from pathlib import Path

class ConstitutionalBlockError(Exception):
    """Raised when a required constitutional artifact is missing."""
    pass

def verify_amendment_artifact() -> bool:
    """
    Check if the amendment_ratified.md artifact exists.
    
    Returns:
        bool: True if the file exists, False otherwise.
        
    Raises:
        ConstitutionalBlockError: If the file is missing, halts execution.
    """
    # Determine the project root relative to this file's location
    # The file is at code/src/constitutional_check.py
    # We need to check specs/001-code-complexity-bug-prediction/amendment_ratified.md
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    amendment_path = project_root / "specs" / "001-code-complexity-bug-prediction" / "amendment_ratified.md"
    
    if not amendment_path.exists():
        raise ConstitutionalBlockError(
            f"ConstitutionalBlockError: Required amendment artifact missing at {amendment_path}. "
            "The pipeline cannot proceed without external governance ratification. "
            "Please wait for the amendment to be ratified and the file to be created."
        )
    
    return True

def main() -> int:
    """
    Main entry point for the constitutional check.
    
    Returns:
        int: Exit code 0 on success, 1 on failure.
    """
    try:
        verify_amendment_artifact()
        print("SUCCESS: Amendment artifact verified. Pipeline can proceed.")
        return 0
    except ConstitutionalBlockError as e:
        print(f"FAILURE: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
