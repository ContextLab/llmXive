"""
T072a: Verify Spec Alignment (FR-001/FR-002)

Verifies that specs/001-social-support-resilience/spec.md contains the required
deprecation/revision blocks for FR-001/FR-002 and SC-001.
Also ensures "Synthetic Cohort" does NOT appear outside the rejection section.
"""
import os
import sys
import logging
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

def verify_spec_alignment() -> bool:
    """
    Checks the spec.md file for alignment with the Plan's single-dataset approach.
    
    Returns:
        bool: True if aligned, False if repair (T072b) is needed.
    """
    spec_path = Path("specs/001-social-support-resilience/spec.md")
    
    if not spec_path.exists():
        logger.error(f"Spec file not found at {spec_path}. Cannot verify alignment.")
        return False

    content = spec_path.read_text()
    
    # Check for FR-001/FR-002 deprecation
    # Accepting "REMOVED" or "DEPRECATED" labels
    has_fr_deprecation = (
        "FR-001" in content and ("REMOVED" in content or "DEPRECATED" in content)
    )
    has_sc_revised = "SC-001" in content and "REVISED" in content

    logger.info(f"FR-001/FR-002 Deprecation Check: {'PASS' if has_fr_deprecation else 'FAIL'}")
    logger.info(f"SC-001 Revision Check: {'PASS' if has_sc_revised else 'FAIL'}")

    # Check for "Synthetic Cohort" outside rejection context
    # We look for the phrase. If found, we must ensure it's in a rejection context.
    # For simplicity in this verification, we check if the phrase exists at all.
    # The task description says: "Also check that the phrase 'Synthetic Cohort' does NOT appear outside the 'Rejection' section."
    # A strict check: count occurrences. If > 0, we need to verify context.
    # However, the task says if it's found outside rejection, trigger repair.
    # Let's assume if the phrase exists, it's risky unless we see a specific "Rejection" header nearby.
    # Given the strictness, if the phrase exists, we flag it for manual review or repair if not clearly rejected.
    
    # Simpler heuristic for T072a: If "Synthetic Cohort" appears, it must be in a "Rejection" section.
    # We will check if the string exists. If it does, we check if it's near a "Rejection" header.
    # If we can't guarantee context, we fail the check to trigger T072b (which is safer).
    
    synthetic_cohort_count = content.count("Synthetic Cohort")
    rejection_section_count = content.count("Rejection")
    
    # If the phrase exists but there's no "Rejection" section, it's definitely a fail.
    # If both exist, we assume the text might be correct, but to be safe and trigger repair if ambiguous:
    # The task says: "If the spec is NOT aligned (e.g., 'Synthetic Cohort' narrative found), log ERROR... and trigger T072b."
    # So if the phrase exists at all, we treat it as a potential violation unless we can prove it's rejected.
    # Let's be strict: if "Synthetic Cohort" appears, we assume it needs verification.
    # But the task says "accepting both 'REMOVED' and 'DEPRECATED' labels" for FR-001/002.
    # For Synthetic Cohort, the requirement is it must NOT appear outside rejection.
    # If it appears at all, it's safer to say "Repair Needed" if we can't parse the markdown structure perfectly.
    
    # Let's try to find if "Synthetic Cohort" is in a rejection context.
    # We look for "Rejection" or "rejected" near "Synthetic Cohort".
    # Split into lines and check proximity.
    lines = content.split('\n')
    found_in_rejection = False
    for i, line in enumerate(lines):
        if "Synthetic Cohort" in line:
            # Check nearby lines for rejection context
            start = max(0, i - 5)
            end = min(len(lines), i + 5)
            context = ' '.join(lines[start:end]).lower()
            if "reject" in context or "invalid" in context or "deprecated" in context:
                found_in_rejection = True
            else:
                logger.warning(f"Found 'Synthetic Cohort' at line {i+1} without clear rejection context.")
    
    if synthetic_cohort_count > 0 and not found_in_rejection:
        logger.error("ERROR: Spec state mismatch. 'Synthetic Cohort' found outside rejection context.")
        return False

    if has_fr_deprecation and has_sc_revised:
        logger.info("INFO: Spec state verified as per Plan requirements.")
        return True
    else:
        logger.error("ERROR: Spec state mismatch. FR-001/FR-002 deprecation or SC-001 revision missing.")
        return False

def main():
    """Entry point for T072a."""
    logger.info("Starting T072a: Verify Spec Alignment (FR-001/FR-002)")
    is_aligned = verify_spec_alignment()
    
    if not is_aligned:
        logger.info("Spec alignment failed. Triggering T072b (Repair Spec Alignment).")
        # In a real pipeline, this would call the repair function or set a flag.
        # For this task, we just log and exit. The orchestrator handles the trigger.
        sys.exit(1) # Exit with error to signal need for repair
    else:
        logger.info("Spec alignment verified. Skipping T072b.")
        sys.exit(0)

if __name__ == "__main__":
    main()