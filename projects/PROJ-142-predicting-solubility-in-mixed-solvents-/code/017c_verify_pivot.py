"""
Task T017c: Verify Pivot Execution.

Verifies that the pivot decision artifact exists and that tasks.md
has been updated if a pivot occurred.
"""
import json
import os
import sys
from pathlib import Path


def verify_pivot_file_exists(pivot_path: Path) -> bool:
    """Check if the pivot decision JSON file exists."""
    if not pivot_path.exists():
        print(f"ERROR: Pivot decision file not found at {pivot_path}", file=sys.stderr)
        return False
    return True


def load_pivot_decision(pivot_path: Path) -> dict:
    """Load and parse the pivot decision JSON file."""
    with open(pivot_path, 'r') as f:
        return json.load(f)


def verify_tasks_md_updated(pivot_decision: dict, tasks_path: Path) -> bool:
    """
    Verify that tasks.md has been updated if the status is 'pivoted'.
    If pivoted, checks for the presence of T017b reference or relevant updates.
    """
    if pivot_decision.get("status") != "pivoted":
        # If not pivoted, no update to tasks.md is strictly required for this check
        return True

    if not tasks_path.exists():
        print(f"ERROR: tasks.md not found at {tasks_path}", file=sys.stderr)
        return False

    with open(tasks_path, 'r') as f:
        content = f.read()

    # Check for evidence of rescope or pivot updates in tasks.md
    # T017b is the task responsible for updating tasks.md.
    # We look for T017b being marked as completed or evidence of the update.
    # The prompt shows T017b is in the completed list, but we verify the file content too.
    
    # Look for T017b task line
    if "- [X] T017b" in content or "- [x] T017b" in content:
        return True
    
    # Fallback: check if the file mentions "pivoted" or "Pure Solvent" in a way that suggests update
    # This is a heuristic if the checkbox isn't strictly parsed correctly
    if "pivoted" in content.lower() and "pure solvent" in content.lower():
        return True

    print("ERROR: tasks.md does not appear to reflect the pivot decision (T017b not marked complete or content not updated).", file=sys.stderr)
    return False


def main():
    """Main entry point for T017c verification."""
    root_dir = Path(__file__).resolve().parent.parent
    pivot_path = root_dir / "data" / "artifacts" / "pivot_decision.json"
    tasks_path = root_dir / "tasks.md"

    print("Verifying Pivot Execution (T017c)...")

    # 1. Verify pivot file exists
    if not verify_pivot_file_exists(pivot_path):
        print("BLOCKING: Pivot execution verification FAILED. Pivot file missing.", file=sys.stderr)
        sys.exit(1)

    # 2. Load pivot decision
    try:
        pivot_decision = load_pivot_decision(pivot_path)
        status = pivot_decision.get("status", "unknown")
        reason = pivot_decision.get("reason", "No reason provided")
        print(f"Pivot Decision Loaded: status={status}, reason={reason}")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in pivot decision file: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Verify tasks.md update if pivoted
    if status == "pivoted":
        print("Status is 'pivoted'. Verifying tasks.md update...")
        if not verify_tasks_md_updated(pivot_decision, tasks_path):
            print("BLOCKING: Pivot execution verification FAILED. tasks.md not updated.", file=sys.stderr)
            sys.exit(1)
        print("SUCCESS: tasks.md has been updated to reflect the pivot.")
    else:
        print("Status is not 'pivoted'. Skipping tasks.md update verification.")

    print("T017c Verification PASSED. Phase 4 can proceed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
