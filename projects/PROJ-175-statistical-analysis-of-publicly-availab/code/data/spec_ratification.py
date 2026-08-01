"""
Spec Amendment Ratification Logic.

Implements T012c: Check plan.md for "Critical Reframe" and create
amendment_ratification_log.json if missing.
"""
import os
import sys
import json
from pathlib import Path

# Project root relative to code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PLAN_PATH = PROJECT_ROOT / "plan.md"
DATA_DIR = PROJECT_ROOT / "data"
RATIFICATION_LOG_PATH = DATA_DIR / "amendment_ratification_log.json"

REQUIRED_AMENDMENT_MARKER = "Critical Reframe"


def check_plan_for_amendment() -> bool:
    """
    Reads plan.md and checks for the required amendment marker.
    Returns True if found, False otherwise.
    """
    if not PLAN_PATH.exists():
        print(f"ERROR: plan.md not found at {PLAN_PATH}", file=sys.stderr)
        return False

    try:
        with open(PLAN_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        return REQUIRED_AMENDMENT_MARKER in content
    except Exception as e:
        print(f"ERROR reading plan.md: {e}", file=sys.stderr)
        return False


def create_ratification_log() -> bool:
    """
    Creates the amendment_ratification_log.json if it does not exist,
    provided the plan.md contains the required marker.
    Returns True on success, False on failure.
    """
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Check if log already exists
    if RATIFICATION_LOG_PATH.exists():
        print(f"Ratification log already exists at {RATIFICATION_LOG_PATH}. Skipping creation.")
        return True

    # Verify plan.md has the marker
    if not check_plan_for_amendment():
        print("ERROR: plan.md does not contain 'Critical Reframe'. Execution blocked.", file=sys.stderr)
        return False

    log_content = {
        "status": "BOOTSTRAPPED",
        "amendment": "FR-001/FR-004/FR-008",
        "rationale": "Plan Critical Reframe detected"
    }

    try:
        with open(RATIFICATION_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(log_content, f, indent=2)
        print(f"Successfully created ratification log at {RATIFICATION_LOG_PATH}")
        return True
    except Exception as e:
        print(f"ERROR writing ratification log: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for T012c."""
    success = create_ratification_log()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
