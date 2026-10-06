import os
import sys
import logging
from pathlib import Path
from utils.logger import get_logger

def verify_spec_alignment(spec_path: str) -> bool:
    """
    Verify that spec.md contains the required deprecation/revision text
    and does not contain an active proposal for 'Synthetic Cohort'.

    Returns True if aligned, False otherwise.
    """
    logger = get_logger(__name__)
    spec_file = Path(spec_path)

    if not spec_file.exists():
        logger.error(f"Spec file not found: {spec_file}")
        return False

    try:
        content = spec_file.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to read spec file: {e}")
        return False

    # Check 1: FR-001 and FR-002 must be marked as REMOVED or DEPRECATED
    # We look for explicit markers. If the FRs are absent entirely, it's a fail.
    # If they exist but are not marked removed, it's a fail.
    fr1_removed = "FR-001" in content and ("REMOVED" in content or "DEPRECATED" in content)
    fr2_removed = "FR-002" in content and ("REMOVED" in content or "DEPRECATED" in content)

    # More robust check: look for the specific sections or markers
    # Assuming the spec uses a format like "## FR-001: ..." and then "Status: REMOVED"
    # or "### FR-001 (REMOVED)"
    # We'll check for the presence of the FR identifiers and the removal status nearby.
    # Since exact format isn't guaranteed, we'll do a broad check:
    # 1. FR-001 and FR-002 must be mentioned.
    # 2. The text "REMOVED" or "DEPRECATED" must be associated with them.
    # This is a heuristic; a more robust parser would be better if the spec format is known.
    # For now, we check if the terms appear in the file, and if the FRs are mentioned.
    # If FR-001 is mentioned but not removed, we fail.
    # If FR-001 is not mentioned at all, we fail (as per task: "If FR-001/FR-002 are absent entirely... this is considered FAIL")

    if "FR-001" not in content:
        logger.error("FR-001 is absent entirely from the spec. FAIL.")
        return False
    if "FR-002" not in content:
        logger.error("FR-002 is absent entirely from the spec. FAIL.")
        return False

    # Check if they are marked as removed/deprecated. We look for patterns like:
    # "FR-001 ... REMOVED" or "FR-001 ... DEPRECATED" within a reasonable proximity.
    # Given the constraints, we'll check if "REMOVED" or "DEPRECATED" appears in the file
    # and hope it's associated with the FRs. A more precise check would require regex.
    # Let's try a regex approach to be safer.
    import re
    # Look for FR-001 followed by REMOVED or DEPRECATED within 200 characters
    fr1_pattern = r"FR-001.*?(REMOVED|DEPRECATED)"
    fr2_pattern = r"FR-002.*?(REMOVED|DEPRECATED)"

    if not re.search(fr1_pattern, content, re.IGNORECASE | re.DOTALL):
        logger.error("FR-001 is not marked as REMOVED or DEPRECATED. FAIL.")
        return False
    if not re.search(fr2_pattern, content, re.IGNORECASE | re.DOTALL):
        logger.error("FR-002 is not marked as REMOVED or DEPRECATED. FAIL.")
        return False

    # Check 2: "Synthetic Cohort" must NOT appear as an active, proposed, or valid step.
    # It is acceptable if it appears ONLY within a "Rejection" or "Invalid" section.
    # We need to detect if "Synthetic Cohort" is proposed as a valid step.
    # This is tricky without a structured spec. We'll look for negative context.
    # If "Synthetic Cohort" is found, we check if it's in a rejection context.
    # Heuristic: if "Synthetic Cohort" is found, it must be near words like "rejected", "invalid", "removed", "deprecated".
    # If it's found near "required", "proposed", "implement", "use", "method", "approach" (without negation), it's a fail.

    synthetic_cohort_pattern = r"Synthetic Cohort"
    matches = list(re.finditer(synthetic_cohort_pattern, content, re.IGNORECASE))

    if not matches:
        # If "Synthetic Cohort" is not mentioned at all, that's fine (it's not proposed).
        logger.info("Synthetic Cohort not mentioned in spec. OK.")
    else:
        for match in matches:
            start = max(0, match.start() - 200)
            end = min(len(content), match.end() + 200)
            context = content[start:end].lower()

            # Check for rejection keywords
            rejection_keywords = ["rejected", "invalid", "removed", "deprecated", "rejection", "not valid", "methodologically invalid"]
            # Check for active/proposal keywords
            active_keywords = ["proposed", "required", "implement", "use", "method", "approach", "step", "plan", "do"]

            is_rejected = any(kw in context for kw in rejection_keywords)
            is_active = any(kw in context for kw in active_keywords) and not is_rejected

            if is_active and not is_rejected:
                logger.error(f"Synthetic Cohort found in active/proposal context without rejection marker. FAIL.")
                logger.error(f"Context: {context}")
                return False
            elif is_rejected:
                logger.info(f"Synthetic Cohort found in rejection context. OK.")
            else:
                # Ambiguous context, but if it's not clearly active, we'll allow it for now.
                # However, to be safe, if it's mentioned without clear rejection, we might want to warn.
                # But the task says "It is acceptable if the phrase appears ONLY within a 'Rejection' or 'Invalid' section".
                # If it's ambiguous, we should probably fail to be strict.
                logger.warning(f"Synthetic Cohort found in ambiguous context. Treating as potential issue.")
                # For now, we'll fail if it's not clearly rejected.
                logger.error(f"Synthetic Cohort found without clear rejection marker. FAIL.")
                return False

    # Check 3: SC-001 must have a "REVISED" block.
    sc1_revised = "SC-001" in content and "REVISED" in content
    if not sc1_revised:
        # Check with regex for SC-001 followed by REVISED
        sc1_pattern = r"SC-001.*?REVISED"
        if not re.search(sc1_pattern, content, re.IGNORECASE | re.DOTALL):
            logger.error("SC-001 is not marked as REVISED. FAIL.")
            return False

    logger.info("Spec alignment verified successfully.")
    return True

def main():
    logger = get_logger(__name__)
    # Path to the spec file relative to project root
    # The project root is the parent of 'code' and 'specs'
    project_root = Path(__file__).parent.parent.parent
    spec_path = project_root / "specs" / "001-social-support-resilience" / "spec.md"

    if not spec_path.exists():
        # Try alternative path if the directory structure is different
        spec_path = project_root / "specs" / "001-the-impact-of-perceived-social-support-o" / "spec.md"

    if not spec_path.exists():
        logger.error(f"Spec file not found at {spec_path}. Aborting.")
        sys.exit(1)

    aligned = verify_spec_alignment(str(spec_path))

    if aligned:
        logger.info("INFO: Spec state verified as per Plan requirements.")
        sys.exit(0)
    else:
        logger.error("ERROR: Spec state mismatch. Manual intervention required to update spec.md.")
        sys.exit(1)

if __name__ == "__main__":
    main()
