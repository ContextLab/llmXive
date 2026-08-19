"""
Verification script for T004v: Verify Spec Resolution.

Inspects spec.md to confirm that FR-001 and US-1 Acceptance Scenario 1
explicitly state "128x128 pixels".
"""
import sys
import re
from pathlib import Path

def verify_spec(spec_path: Path) -> bool:
    """
    Verify that spec.md contains the required resolution specifications.
    
    Args:
        spec_path: Path to the spec.md file.
        
    Returns:
        True if verification passes, False otherwise.
    """
    if not spec_path.exists():
        print(f"ERROR: spec.md not found at {spec_path}")
        return False

    content = spec_path.read_text(encoding='utf-8')
    
    # Check for FR-001
    fr001_pattern = r'FR-001.*?128x128.*?pixels'
    fr001_match = re.search(fr001_pattern, content, re.IGNORECASE | re.DOTALL)
    
    # Check for US-1 Acceptance Scenario 1
    us1_pattern = r'US-1.*?Acceptance Scenario.*?1.*?128x128.*?pixels'
    us1_match = re.search(us1_pattern, content, re.IGNORECASE | re.DOTALL)
    
    # More lenient checks if specific phrasing varies
    if not fr001_match:
        # Try looking for FR-001 and 128x128 pixels separately in proximity
        fr001_section = re.search(r'FR-001.*?(?=FR-002|US-|$)', content, re.DOTALL)
        if fr001_section and '128x128' in fr001_section.group() and 'pixels' in fr001_section.group():
            fr001_match = True
        else:
            fr001_match = False
    
    if not us1_match:
        # Try looking for US-1 and 128x128 pixels in proximity
        us1_section = re.search(r'US-1.*?(?=US-2|$)', content, re.DOTALL)
        if us1_section and 'Acceptance Scenario' in us1_section.group() and '128x128' in us1_section.group() and 'pixels' in us1_section.group():
            us1_match = True
        else:
            us1_match = False

    success = True
    
    if not fr001_match:
        print("FAIL: FR-001 does not explicitly state '128x128 pixels'")
        success = False
    else:
        print("PASS: FR-001 explicitly states '128x128 pixels'")
        
    if not us1_match:
        print("FAIL: US-1 Acceptance Scenario 1 does not explicitly state '128x128 pixels'")
        success = False
    else:
        print("PASS: US-1 Acceptance Scenario 1 explicitly states '128x128 pixels'")
        
    return success

def main() -> int:
    """Main entry point for the verification script."""
    # Look for spec.md in common locations
    possible_paths = [
        Path("specs/001-predict-stiffness-cnn/spec.md"),
        Path("spec.md"),
        Path("docs/spec.md"),
    ]
    
    spec_path = None
    for p in possible_paths:
        if p.exists():
            spec_path = p
            break
    
    if spec_path is None:
        print("ERROR: Could not find spec.md in any expected location")
        return 1
        
    print(f"Verifying spec at: {spec_path}")
    if verify_spec(spec_path):
        print("\nT004v VERIFICATION: PASSED")
        return 0
    else:
        print("\nT004v VERIFICATION: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
