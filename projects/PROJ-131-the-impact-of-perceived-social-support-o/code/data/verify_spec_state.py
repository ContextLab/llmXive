"""
Task T041: Verify Spec State
Confirms that specs/001-social-support-resilience/spec.md contains:
1. "DEPRECATED" blocks for FR-001/FR-002
2. "REVISED" block for SC-001
"""
import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_spec_state():
    """
    Reads the spec file and asserts the presence of required deprecation/revision text.
    """
    # Define the path to the spec file relative to the project root
    # Assuming this script runs from the project root or code/ directory
    project_root = Path(__file__).resolve().parent.parent
    spec_path = project_root / "specs" / "001-social-support-resilience" / "spec.md"

    if not spec_path.exists():
        logger.error(f"Spec file not found at: {spec_path}")
        sys.exit(1)

    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read spec file: {e}")
        sys.exit(1)

    # Check for required markers
    checks = {
        "FR-001 Deprecated": "DEPRECATED" in content and "FR-001" in content,
        "FR-002 Deprecated": "DEPRECATED" in content and "FR-002" in content,
        "SC-001 Revised": "REVISED" in content and "SC-001" in content,
        "Synthetic Cohort Removed": "Synthetic Cohort" not in content or "removed" in content.lower() or "deprecated" in content.lower()
    }

    all_passed = True
    for check_name, result in checks.items():
        if result:
            logger.info(f"✓ {check_name}: PASSED")
        else:
            logger.error(f"✗ {check_name}: FAILED")
            all_passed = False

    if all_passed:
        logger.info("INFO: Spec state verified as per Plan requirements.")
        return True
    else:
        logger.error("ERROR: Spec state mismatch. Required markers not found.")
        return False

if __name__ == "__main__":
    success = verify_spec_state()
    sys.exit(0 if success else 1)
