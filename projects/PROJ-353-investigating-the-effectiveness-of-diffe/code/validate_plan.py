"""
Validation script to ensure plan.md and spec.md alignment with research constraints.

This script verifies that:
1. spec.md contains "N=110" (FR-001)
2. plan.md contains "Tobit Regression", "Cox Proportional Hazards", and "0.90"

Exits with code 1 if any check fails.
"""
import sys
from pathlib import Path

def validate_files():
    """Run validation checks on spec.md and plan.md."""
    project_root = Path(__file__).parent.parent
    spec_path = project_root / "specs" / "353-loss-functions-small-world" / "spec.md"
    plan_path = project_root / "specs" / "353-loss-functions-small-world" / "plan.md"

    # Check if files exist
    if not spec_path.exists():
        print(f"ERROR: spec.md not found at {spec_path}")
        sys.exit(1)
    
    if not plan_path.exists():
        print(f"ERROR: plan.md not found at {plan_path}")
        sys.exit(1)

    # Read content
    spec_content = spec_path.read_text()
    plan_content = plan_path.read_text()

    # Check 1: spec.md must contain "N=110"
    if "N=110" not in spec_content:
        print("ERROR: spec.md does not contain 'N=110' (FR-001 constraint)")
        sys.exit(1)
    print("PASS: spec.md contains 'N=110'")

    # Check 2: plan.md must contain "Tobit Regression"
    if "Tobit Regression" not in plan_content:
        print("ERROR: plan.md does not contain 'Tobit Regression'")
        sys.exit(1)
    print("PASS: plan.md contains 'Tobit Regression'")

    # Check 3: plan.md must contain "Cox Proportional Hazards"
    if "Cox Proportional Hazards" not in plan_content:
        print("ERROR: plan.md does not contain 'Cox Proportional Hazards'")
        sys.exit(1)
    print("PASS: plan.md contains 'Cox Proportional Hazards'")

    # Check 4: plan.md must contain "0.90"
    if "0.90" not in plan_content:
        print("ERROR: plan.md does not contain '0.90' (convergence threshold)")
        sys.exit(1)
    print("PASS: plan.md contains '0.90'")

    print("\nAll validation checks passed.")

if __name__ == "__main__":
    validate_files()