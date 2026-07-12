"""
T017c: Verify Pivot Execution.

This script verifies that the pivot logic (T017) has been executed correctly
by checking for the existence of data/artifacts/pivot_decision.json.
Additionally, if the pivot status is "pivoted", it verifies that T017b
(rescope_tasks) has updated tasks.md accordingly.

If verification fails, it exits with code 1 and prints an error.
"""
import json
import os
import sys
from pathlib import Path

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PIVOT_DECISION_PATH = PROJECT_ROOT / "data" / "artifacts" / "pivot_decision.json"
TASKS_MD_PATH = PROJECT_ROOT / "tasks.md"

def verify_pivot_file_exists() -> bool:
    """Check if pivot_decision.json exists."""
    if not PIVOT_DECISION_PATH.exists():
        print(f"ERROR: Pivot decision file not found at {PIVOT_DECISION_PATH}", file=sys.stderr)
        return False
    return True

def load_pivot_decision() -> dict:
    """Load and parse the pivot decision JSON."""
    try:
        with open(PIVOT_DECISION_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {PIVOT_DECISION_PATH}: {e}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"ERROR: Failed to read {PIVOT_DECISION_PATH}: {e}", file=sys.stderr)
        return {}

def verify_tasks_md_updated(pivot_status: str) -> bool:
    """
    If pivot_status is 'pivoted', verify tasks.md has been updated.
    Update logic: T017b should have modified tasks.md to redefine US2/US3
    success criteria for pure solvents.
    """
    if pivot_status != "pivoted":
        # No update required if not pivoted
        return True

    if not TASKS_MD_PATH.exists():
        print(f"ERROR: tasks.md not found at {TASKS_MD_PATH}", file=sys.stderr)
        return False

    try:
        with open(TASKS_MD_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"ERROR: Failed to read tasks.md: {e}", file=sys.stderr)
        return False

    # Check for evidence of update (e.g., mention of "pure solvent" or "re-scoped")
    # T017b should have updated the file. We look for indicators that the update happened.
    # A robust check might look for specific markers, but a simple presence check for
    # "pure solvent" context in US2/US3 sections is a good proxy if the file was modified.
    # However, since we are verifying T017b's work, we check if the file contains
    # evidence that the scope was re-defined.
    
    # Heuristic: If pivoted, tasks.md should contain text indicating the pivot 
    # and the re-scoping. We check for the presence of "pure solvent" in the context 
    # of US2/US3 or a specific marker if T017b added one.
    # Given T017b implementation, it likely updated the text.
    
    # Let's check if the file has been modified recently or contains specific 
    # re-scoping language. Since we can't rely on timestamps across runs, 
    # we check content.
    
    # If pivoted, we expect the tasks.md to reflect the new reality.
    # We look for "pure solvent" in the description of US2 or US3.
    us2_section = content.find("## Phase 4: User Story 2")
    us3_section = content.find("## Phase 5: User Story 3")
    
    if us2_section == -1 or us3_section == -1:
        print("ERROR: Could not find US2 or US3 sections in tasks.md", file=sys.stderr)
        return False
    
    us2_content = content[us2_section:us3_section]
    us3_content = content[us3_section:]
    
    # Check if "pure solvent" or similar re-scoping language is present in US2/US3
    # This assumes T017b added this text.
    has_pure_solvent_ref = "pure solvent" in us2_content.lower() or "pure solvent" in us3_content.lower()
    
    # If the pivot says "pivoted", but tasks.md doesn't reflect it, fail.
    if not has_pure_solvent_ref:
        print("ERROR: Pivot status is 'pivoted' but tasks.md does not appear to be re-scoped for pure solvents.", file=sys.stderr)
        print("Ensure T017b has been executed to update tasks.md.", file=sys.stderr)
        return False
    
    return True

def main():
    print("Starting T017c: Verify Pivot Execution...")
    
    # Step 1: Check if pivot_decision.json exists
    if not verify_pivot_file_exists():
        print("VERIFICATION FAILED: Pivot decision file missing.")
        sys.exit(1)
    
    # Step 2: Load pivot decision
    pivot_data = load_pivot_decision()
    if not pivot_data:
        print("VERIFICATION FAILED: Could not load pivot decision data.")
        sys.exit(1)
    
    status = pivot_data.get("status", "")
    reason = pivot_data.get("reason", "N/A")
    
    print(f"Pivot Status: {status}")
    print(f"Reason: {reason}")
    
    # Step 3: If pivoted, verify tasks.md update
    if status == "pivoted":
        print("Pivot status is 'pivoted'. Verifying tasks.md update...")
        if not verify_tasks_md_updated(status):
            print("VERIFICATION FAILED: tasks.md not updated for pivoted state.")
            sys.exit(1)
        print("tasks.md update verified successfully.")
    else:
        print("Pivot status is not 'pivoted'. No tasks.md update required.")
    
    print("VERIFICATION PASSED: Pivot execution verified.")
    sys.exit(0)

if __name__ == "__main__":
    main()