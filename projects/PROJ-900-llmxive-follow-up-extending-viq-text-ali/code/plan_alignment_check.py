"""
Script to verify that plan.md references the correct spec requirement (SC-004)
and does not contain the erroneous SC-005 reference.

This script fulfills the verification aspect of Task T036b.
"""
import os
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    plan_path = project_root / "plan.md"
    
    if not plan_path.exists():
        print(f"ERROR: {plan_path} not found.")
        sys.exit(1)

    with open(plan_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for the erroneous reference
    if "SC-005" in content:
        print("ERROR: plan.md still contains a reference to 'SC-005'.")
        print("This contradicts the spec which uses SC-004 for paired t-test/Wilcoxon.")
        print("Please update plan.md to remove this reference.")
        sys.exit(1)

    # Check for the correct reference
    if "SC-004" not in content:
        print("WARNING: plan.md does not explicitly mention 'SC-004'.")
        print("While SC-005 is gone, SC-004 should be referenced in the Spec Amendments section.")
        # We do not fail here, as the task is primarily to remove SC-005, 
        # but we flag it for review.
    else:
        print("SUCCESS: plan.md correctly references SC-004 and does not contain SC-005.")
        
    # Verify the Decision Record exists
    decision_path = project_root / "decisions" / "003-plan-spec-alignment.md"
    if not decision_path.exists():
        print(f"WARNING: Decision record {decision_path} not found.")
        print("Please ensure the decision record documenting this change exists.")
    else:
        print(f"SUCCESS: Decision record found at {decision_path}")

    sys.exit(0)

if __name__ == "__main__":
    main()