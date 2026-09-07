"""
T062: Verify Methodology & Reporting

Checks:
1. `data-model.md` contains explicit contrast with standard OLS.
2. `plan.md` contains the uncertainty visualization logic.
3. `plan.md` contains the report disclaimer requirements.

Exit 0 if all checks pass, Exit 1 otherwise.
"""
import sys
import re
from pathlib import Path

def load_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return path.read_text(encoding="utf-8")

def check_ols_contrast(content: str) -> bool:
    """Check for explicit contrast with standard OLS in data-model.md."""
    # Look for keywords indicating contrast or methodological distinction
    patterns = [
        r"robust\s+standard\s+errors",
        r"HC3",
        r"cluster-robust",
        r"different\s+from\s+standard\s+OLS",
        r"contrast\s+with\s+OLS",
        r"deviation\s+from\s+OLS",
        r"alternative\s+to\s+OLS",
        r"unlike\s+standard\s+OLS"
    ]
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False

def check_uncertainty_logic(content: str) -> bool:
    """Check for uncertainty visualization logic in plan.md."""
    patterns = [
        r"uncertainty\s+visualization",
        r"confidence\s+interval",
        r"error\s+bars",
        r"sensitivity\s+plot",
        r"coefficient\s+variation"
    ]
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False

def check_disclaimer_requirements(content: str) -> bool:
    """Check for report disclaimer requirements in plan.md."""
    patterns = [
        r"associational\s+nature",
        r"observational\s+design",
        r"disclaimer",
        r"not\s+causal",
        r"correlation\s+does\s+not\s+imply\s+causation"
    ]
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False

def main():
    project_root = Path(__file__).parent.parent
    data_model_path = project_root / "data-model.md"
    plan_path = project_root / "plan.md"

    try:
        data_model_content = load_file(data_model_path)
        plan_content = load_file(plan_path)
    except FileNotFoundError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)

    # Check 1: data-model.md OLS contrast
    if not check_ols_contrast(data_model_content):
        print("FAIL: data-model.md missing explicit contrast with standard OLS.", file=sys.stderr)
        sys.exit(1)

    # Check 2: plan.md uncertainty visualization
    if not check_uncertainty_logic(plan_content):
        print("FAIL: plan.md missing uncertainty visualization logic.", file=sys.stderr)
        sys.exit(1)

    # Check 3: plan.md report disclaimer
    if not check_disclaimer_requirements(plan_content):
        print("FAIL: plan.md missing report disclaimer requirements.", file=sys.stderr)
        sys.exit(1)

    print("SUCCESS: All methodology and reporting checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
