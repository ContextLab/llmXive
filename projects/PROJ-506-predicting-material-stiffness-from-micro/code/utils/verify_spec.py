import sys
import re
from pathlib import Path

def verify_spec() -> bool:
    """
    Verify that spec.md contains the required resolution text:
    1. FR-001 explicitly states "128x128 pixels".
    2. FR-001 references "US-1 Acceptance Scenario 1".
    
    Returns True if both conditions are met, False otherwise.
    """
    spec_path = Path("specs/001-predict-stiffness-cnn/spec.md")
    
    if not spec_path.exists():
        print(f"ERROR: {spec_path} does not exist.")
        return False
    
    try:
        content = spec_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"ERROR: Could not read {spec_path}: {e}")
        return False
    
    # Check for "128x128 pixels"
    if "128x128 pixels" not in content:
        print("ERROR: Spec does not contain '128x128 pixels'.")
        return False
    
    # Check for "US-1 Acceptance Scenario 1"
    if "US-1 Acceptance Scenario 1" not in content:
        print("ERROR: Spec does not contain 'US-1 Acceptance Scenario 1'.")
        return False
    
    print("VERIFIED: Spec.md contains '128x128 pixels' and 'US-1 Acceptance Scenario 1'.")
    return True

def main():
    success = verify_spec()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
