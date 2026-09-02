"""
Verification script for T004v: Verify Spec Resolution.

This script inspects `spec.md` to confirm that FR-001 and US-1 Acceptance Scenario 1
explicitly state "128x128 pixels".
"""
import sys
import re
from pathlib import Path

def verify_spec() -> bool:
    """
    Inspect spec.md for the required resolution text.

    Returns:
        bool: True if the text is found, False otherwise.
    """
    spec_path = Path("specs/001-predict-stiffness-cnn/spec.md")

    if not spec_path.exists():
        print(f"ERROR: {spec_path} does not exist.")
        return False

    content = spec_path.read_text()

    # Check for FR-001 mentioning 128x128
    fr_001_pattern = r"FR-001.*128x128.*pixels|128x128.*pixels.*FR-001"
    fr_001_match = re.search(fr_001_pattern, content, re.IGNORECASE | re.DOTALL)

    # Check for US-1 Acceptance Scenario 1 mentioning 128x128
    us_1_pattern = r"US-1.*Acceptance Scenario 1.*128x128.*pixels|128x128.*pixels.*US-1.*Acceptance Scenario 1"
    us_1_match = re.search(us_1_pattern, content, re.IGNORECASE | re.DOTALL)

    # If the specific combined patterns fail, do a broader search to be robust
    # looking for the specific phrase in the context of FR-001 or US-1
    if not fr_001_match:
        # Look for FR-001 section and check if 128x128 appears nearby
        fr_section = re.search(r"FR-001.*?(?=\n\n|\n#|\n##|$)", content, re.DOTALL)
        if fr_section and "128x128" in fr_section.group() and "pixels" in fr_section.group():
            fr_001_match = True

    if not us_1_match:
        # Look for US-1 Acceptance Scenario 1 section and check if 128x128 appears nearby
        us_section = re.search(r"US-1.*?Acceptance Scenario 1.*?(?=\n\n|\n#|\n##|$)", content, re.DOTALL)
        if us_section and "128x128" in us_section.group() and "pixels" in us_section.group():
            us_1_match = True

    if fr_001_match and us_1_match:
        print("SUCCESS: spec.md contains '128x128 pixels' in both FR-001 and US-1 Acceptance Scenario 1.")
        return True
    else:
        print("FAILURE: Could not confirm '128x128 pixels' in required locations.")
        if not fr_001_match:
            print("  - Missing or incorrect FR-001 reference.")
        if not us_1_match:
            print("  - Missing or incorrect US-1 Acceptance Scenario 1 reference.")
        return False

def main():
    success = verify_spec()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
