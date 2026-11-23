"""
Script to verify methodology and reporting requirements.
Checks data-model.md for OLS contrast and plan.md for uncertainty logic.
"""
import os
import re
import sys
from pathlib import Path

def get_project_root():
    return Path(__file__).resolve().parents[1]

def check_ols_contrast(data_model_content):
    """Check for explicit contrast with standard OLS."""
    if "OLS" in data_model_content or "Ordinary Least Squares" in data_model_content:
        # Check for contrast words
        if re.search(r'different|contrast|unlike|versus|alternative', data_model_content, re.IGNORECASE):
            return True, "Explicit contrast with OLS found."
    return False, "No explicit contrast with standard OLS found in data-model.md."

def check_uncertainty_logic(plan_content):
    """Check for uncertainty visualization logic and disclaimer requirements."""
    if "uncertainty" in plan_content.lower():
        if re.search(r'visual|plot|disclaimer|warning', plan_content, re.IGNORECASE):
            return True, "Uncertainty visualization and disclaimer logic found."
    return False, "Uncertainty visualization/disclaimer logic not found in plan.md."

def main():
    project_root = get_project_root()
    data_model_path = project_root / "specs" / "001-agriculture-optimization" / "data-model.md"
    plan_path = project_root / "specs" / "001-agriculture-optimization" / "plan.md"

    if not data_model_path.exists():
        print(f"Error: {data_model_path} not found.")
        sys.exit(1)
    if not plan_path.exists():
        print(f"Error: {plan_path} not found.")
        sys.exit(1)

    data_model_content = data_model_path.read_text()
    plan_content = plan_path.read_text()
    errors = []

    # Check OLS Contrast
    ols_ok, ols_msg = check_ols_contrast(data_model_content)
    if not ols_ok:
        errors.append(ols_msg)

    # Check Uncertainty Logic
    unc_ok, unc_msg = check_uncertainty_logic(plan_content)
    if not unc_ok:
        errors.append(unc_msg)

    if errors:
        print("Methodology & Reporting Verification FAILED:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("Methodology & Reporting Verification PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()