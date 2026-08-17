import sys
from pathlib import Path
import re

def verify_spec_anova() -> bool:
    """
    Verify that spec.md contains the required statistical method references:
    - FR-007
    - SC-004
    - US-3 Acceptance Scenario 2
    
    All must explicitly state "One-way ANOVA and Tukey HSD".
    
    Returns:
        bool: True if all requirements are met, False otherwise.
    """
    spec_path = Path("specs/001-predict-stiffness-cnn/spec.md")
    
    if not spec_path.exists():
        print(f"ERROR: spec.md not found at {spec_path}")
        return False
    
    content = spec_path.read_text()
    
    required_text = "One-way ANOVA and Tukey HSD"
    checks = [
        ("FR-007", r"FR-007.*?" + re.escape(required_text)),
        ("SC-004", r"SC-004.*?" + re.escape(required_text)),
        ("US-3 Acceptance Scenario 2", r"US-3.*?Acceptance Scenario 2.*?" + re.escape(required_text)),
    ]
    
    all_passed = True
    
    for check_name, pattern in checks:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            print(f"✓ PASS: {check_name} explicitly states '{required_text}'")
        else:
            print(f"✗ FAIL: {check_name} does NOT explicitly state '{required_text}'")
            all_passed = False
    
    return all_passed

def main():
    print("Verifying spec.md for One-way ANOVA and Tukey HSD references...")
    success = verify_spec_anova()
    
    if success:
        print("\n✅ All gate checks passed. Proceeding to Phase 1.")
        sys.exit(0)
    else:
        print("\n❌ Gate check failed. Spec must be updated before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()