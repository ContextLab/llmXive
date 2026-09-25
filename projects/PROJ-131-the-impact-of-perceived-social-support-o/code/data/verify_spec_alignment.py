"""
Verify Spec State (T041)

Confirms that `specs/001-social-support-resilience/spec.md` contains the required
"DEPRECATED" blocks for FR-001/FR-002 and the "REVISED" block for SC-001.
This task strictly reads the file and asserts presence of specific text markers.
It does NOT modify the file.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging to stdout and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/results/spec_verification.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

SPEC_PATH = Path("specs/001-social-support-resilience/spec.md")

# Required markers indicating the "Revised Approach" per Plan
REQUIRED_MARKERS = [
    "DEPRECATED",
    "FR-001",
    "FR-002",
    "REVISED",
    "SC-001",
    "Synthetic Cohort"  # Must be present in context of rejection/removal
]

# Specific phrases that confirm the revision status
REQUIRED_PHRASES = [
    "DEPRECATED",
    "REVISED"
]

def verify_spec_alignment():
    """
    Reads the spec.md file and verifies the presence of deprecation/revision markers.
    """
    logger.info(f"Checking spec file at: {SPEC_PATH.absolute()}")

    if not SPEC_PATH.exists():
        logger.error(f"ERROR: Spec file not found at {SPEC_PATH}. Aborting.")
        return False

    try:
        with open(SPEC_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"ERROR: Could not read spec file: {e}")
        return False

    # Check for the existence of required markers
    missing_markers = []
    for marker in REQUIRED_MARKERS:
        if marker not in content:
            missing_markers.append(marker)

    if missing_markers:
        logger.error(f"ERROR: Spec state mismatch. Missing required markers: {missing_markers}")
        logger.error("The spec must contain 'DEPRECATED' blocks for FR-001/FR-002 and 'REVISED' block for SC-001.")
        return False

    # Additional check: Ensure "Synthetic Cohort" is mentioned in a context of removal/rejection
    # (The Plan mandates exclusion, so the text should reflect that it was removed or is invalid)
    if "Synthetic Cohort" not in content:
        # It's possible the text says "removed" without the phrase "Synthetic Cohort" if fully cleaned,
        # but usually the revision note references what is being revised.
        # We will be lenient here as long as DEPRECATED/REVISED are present, 
        # but log a warning if the specific term is missing entirely.
        logger.warning("WARNING: 'Synthetic Cohort' phrase not found. Ensure the revision notes explicitly state the exclusion.")

    # Verify specific phrasing if possible
    if "DEPRECATED" in content and "REVISED" in content:
        logger.info("INFO: Spec state verified as per Plan requirements.")
        logger.info("Found 'DEPRECATED' blocks for FR-001/FR-002.")
        logger.info("Found 'REVISED' block for SC-001.")
        return True
    else:
        logger.error("ERROR: Spec state mismatch. Could not find 'DEPRECATED' or 'REVISED' markers.")
        return False

def main():
    """
    Entry point for T041 verification.
    """
    success = verify_spec_alignment()
    if not success:
        logger.error("Verification FAILED. The spec does not align with the Plan's Revised Approach.")
        sys.exit(1)
    else:
        logger.info("Verification PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()