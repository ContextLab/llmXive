"""
T000b: Plan Verification Gate.
Verifies that plan.md explicitly states "DementiaBank is explicitly excluded"
in the Scope Constraint section.
"""
import sys
from pathlib import Path

def verify_plan_gate():
    plan_path = Path("plan.md")
    if not plan_path.exists():
        print("FAIL: plan.md not found.")
        sys.exit(1)

    content = plan_path.read_text(encoding="utf-8")
    target_phrase = "DementiaBank is explicitly excluded"

    # Check for the exact phrase in the content
    if target_phrase in content:
        print("PASS: Plan verification gate successful.")
        print(f"Found: '{target_phrase}' in plan.md")
        return True
    else:
        print("FAIL: Plan verification gate failed.")
        print(f"Missing required phrase: '{target_phrase}'")
        print("This task blocks the pipeline.")
        sys.exit(1)

if __name__ == "__main__":
    verify_plan_gate()
