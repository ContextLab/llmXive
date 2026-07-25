"""
Task T008: Create and verify directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/specs/001-llmxive-drift-detection/`

This module ensures the existence of the specific drift detection specs directory
required for the project's design documents.
"""
import os
import sys
from pathlib import Path

# Project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Target directory for T008
DRIFT_DETECTION_SPECS_DIR = PROJECT_ROOT / "specs" / "001-llmxive-drift-detection"


def ensure_drift_detection_specs_directory() -> bool:
    """
    Creates the drift detection specs directory if it does not exist.
    Verifies its existence after creation.

    Returns:
        bool: True if the directory exists (created or pre-existing), False otherwise.
    """
    try:
        # Create parents if they don't exist (though specs should exist from T006)
        DRIFT_DETECTION_SPECS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Verify the directory actually exists and is a directory
        if not DRIFT_DETECTION_SPECS_DIR.exists():
            print(f"ERROR: Directory {DRIFT_DETECTION_SPECS_DIR} was not created.", file=sys.stderr)
            return False
        
        if not DRIFT_DETECTION_SPECS_DIR.is_dir():
            print(f"ERROR: Path {DRIFT_DETECTION_SPECS_DIR} exists but is not a directory.", file=sys.stderr)
            return False

        print(f"Successfully verified directory: {DRIFT_DETECTION_SPECS_DIR}")
        return True

    except PermissionError as e:
        print(f"ERROR: Permission denied creating directory {DRIFT_DETECTION_SPECS_DIR}: {e}", file=sys.stderr)
        return False
    except OSError as e:
        print(f"ERROR: OS error creating directory {DRIFT_DETECTION_SPECS_DIR}: {e}", file=sys.stderr)
        return False


def main() -> int:
    """
    Main entry point for the script.
    Returns 0 on success, 1 on failure.
    """
    print(f"Ensuring drift detection specs directory exists at: {DRIFT_DETECTION_SPECS_DIR}")
    success = ensure_drift_detection_specs_directory()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())