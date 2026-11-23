"""
Validation script to ensure plan.md and spec.md alignment with research constraints.

This script verifies that:
1. spec.md contains "N=110" (FR-001)
2. plan.md contains "Tobit Regression", "Cox Proportional Hazards", "0.90",
   AND the phrase "interaction terms" or "interaction focus" (FR-008).

Constraint: If values do not match, the script MUST log a WARNING but NOT exit with code 1
to avoid circular build failure during the foundational phase.
"""
import sys
from pathlib import Path

# Project root is two levels up from code/validate_plan.py
PROJECT_ROOT = Path(__file__).parent.parent
SPEC_PATH = PROJECT_ROOT / "specs" / "001-investigating-the-effectiveness-of-diffe" / "spec.md"
PLAN_PATH = PROJECT_ROOT / "specs" / "001-investigating-the-effectiveness-of-diffe" / "plan.md"

def validate_files():
    """Run validation checks on spec.md and plan.md."""
    
    # Check if files exist
    if not SPEC_PATH.exists():
        print(f"WARNING: spec.md not found at {SPEC_PATH}")
        print("WARNING: Cannot validate FR-001 (N=110).")
        # Do not exit with 1 to avoid circular build failure
        return
    
    if not PLAN_PATH.exists():
        print(f"WARNING: plan.md not found at {PLAN_PATH}")
        print("WARNING: Cannot validate FR-008 and convergence threshold.")
        # Do not exit with 1 to avoid circular build failure
        return

    # Read content
    spec_content = SPEC_PATH.read_text()
    plan_content = PLAN_PATH.read_text()

    # Check 1: spec.md must contain "N=110" (FR-001)
    if "N=110" in spec_content:
        print("PASS: spec.md contains 'N=110' (FR-001)")
    else:
        print("WARNING: spec.md does not contain 'N=110' (FR-001 constraint)")

    # Check 2: plan.md must contain "Tobit Regression"
    if "Tobit Regression" in plan_content:
        print("PASS: plan.md contains 'Tobit Regression'")
    else:
        print("WARNING: plan.md does not contain 'Tobit Regression'")

    # Check 3: plan.md must contain "Cox Proportional Hazards"
    if "Cox Proportional Hazards" in plan_content:
        print("PASS: plan.md contains 'Cox Proportional Hazards'")
    else:
        print("WARNING: plan.md does not contain 'Cox Proportional Hazards'")

    # Check 4: plan.md must contain "0.90" (Convergence Threshold)
    if "0.90" in plan_content:
        print("PASS: plan.md contains '0.90' (convergence threshold)")
    else:
        print("WARNING: plan.md does not contain '0.90' (convergence threshold)")

    # Check 5: plan.md must contain "interaction terms" or "interaction focus" (FR-008)
    has_interaction_terms = "interaction terms" in plan_content.lower()
    has_interaction_focus = "interaction focus" in plan_content.lower()
    
    if has_interaction_terms or has_interaction_focus:
        print("PASS: plan.md contains interaction focus/terms (FR-008)")
    else:
        print("WARNING: plan.md does not contain 'interaction terms' or 'interaction focus' (FR-008)")

    print("\nValidation complete. See warnings above if any checks failed.")

if __name__ == "__main__":
    validate_files()