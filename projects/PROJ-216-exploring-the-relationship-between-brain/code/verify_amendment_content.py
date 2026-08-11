"""
Verify that the Spec Amendment artifact contains the required overridden requirements.
Task: T008c
"""
import sys
from pathlib import Path

REQUIRED_STRINGS = [
    "FR-001",
    "FR-005",
    "SC-001",
    "SC-004"
]

AMENDMENT_PATH = Path("specs/amendment-001-fluid-intelligence-n10.md")

def verify_amendment_content() -> bool:
    """
    Verifies that the amendment file exists and contains all required requirement IDs.
    Returns True if all checks pass, False otherwise.
    """
    if not AMENDMENT_PATH.exists():
        print(f"ERROR: Amendment file not found at {AMENDMENT_PATH}")
        return False

    content = AMENDMENT_PATH.read_text(encoding="utf-8")
    
    missing = []
    for req_id in REQUIRED_STRINGS:
        if req_id not in content:
            missing.append(req_id)

    if missing:
        print(f"ERROR: The following required requirement IDs are missing from the amendment: {missing}")
        print("Verification FAILED.")
        return False

    print(f"SUCCESS: All required requirement IDs found in {AMENDMENT_PATH.name}")
    for req_id in REQUIRED_STRINGS:
        print(f"  - Found: {req_id}")
    print("Verification PASSED.")
    return True

def main():
    success = verify_amendment_content()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
