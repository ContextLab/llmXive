import sys
from pathlib import Path
import re

def verify_spec() -> bool:
    """
    Verify that spec.md contains the required resolution text:
    - FR-001
    - US-1 Acceptance Scenario 1
    
    Both must explicitly state "128x128 pixels".
    
    Returns:
        bool: True if all requirements are met, False otherwise.
    """
    spec_path = Path("specs/001-predict-stiffness-cnn/spec.md")
    
    if not spec_path.exists():
        print(f"ERROR: spec.md not found at {spec_path}")
        return False
    
    content = spec_path.read_text()
    
    required_text = "128x128 pixels"
    checks = [
        ("FR-001", r"FR-001.*?" + re.escape(required_text)),
        ("US-1 Acceptance Scenario 1", r"US-1.*?Acceptance Scenario 1.*?" + re.escape(required_text)),
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
    print("Verifying spec.md for 128x128 pixels resolution...")
    success = verify_spec()
    
    if success:
        print("\n✅ Spec resolution verified.")
        sys.exit(0)
    else:
        print("\n❌ Spec resolution verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()