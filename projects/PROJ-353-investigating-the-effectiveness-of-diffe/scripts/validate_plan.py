import sys
from pathlib import Path

def validate_plan():
    """
    Validates that plan.md contains specific required strings.
    If values are missing, logs a warning to stdout but does NOT fail the build.
    """
    plan_path = Path("plan.md")
    
    if not plan_path.exists():
        print("WARNING: plan.md not found in project root.")
        return

    content = plan_path.read_text()
    
    required_strings = [
        "N=110",
        "Tobit Regression",
        "Cox Proportional Hazards",
        "0.90"
    ]
    
    missing = []
    for req in required_strings:
        if req not in content:
            missing.append(req)
    
    if missing:
        print("WARNING: The following required strings were not found in plan.md:")
        for item in missing:
            print(f"  - {item}")
        print("Continuing build (validation warning only).")
    else:
        print("SUCCESS: All required strings found in plan.md.")

if __name__ == "__main__":
    validate_plan()