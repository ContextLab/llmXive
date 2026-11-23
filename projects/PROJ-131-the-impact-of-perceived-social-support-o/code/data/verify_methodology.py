import os
import sys
import logging
from pathlib import Path
import json
from utils.logger import get_logger

def find_section_5(file_path: Path) -> str:
    """
    Locates Section 5 'Methodological Notes' in the spec.md file.
    Returns the content of the section or an empty string if not found.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Spec file not found: {file_path}")

    content = file_path.read_text(encoding='utf-8')
    lines = content.splitlines()

    section_start = -1
    section_end = len(lines)

    # Look for Section 5 header
    for i, line in enumerate(lines):
        if line.strip().startswith("## 5. Methodological Notes") or \
           line.strip().startswith("# 5. Methodological Notes") or \
           line.strip().startswith("5. Methodological Notes"):
            section_start = i
            break

    if section_start == -1:
        # Try a more flexible search for "Methodological Notes"
        for i, line in enumerate(lines):
            if "Methodological Notes" in line:
                section_start = i
                break

    if section_start == -1:
        return ""

    # Find the next section header (## or #) to determine end
    for i in range(section_start + 1, len(lines)):
        if lines[i].strip().startswith("##") or lines[i].strip().startswith("#"):
            section_end = i
            break

    return "\n".join(lines[section_start:section_end])

def verify_alignment(section_content: str, logger: logging.Logger) -> bool:
    """
    Verifies that Section 5 contains the 'Revised Approach' rationale
    and handles 'Synthetic Cohort' correctly (only in rejection context).
    """
    is_aligned = True

    # 1. Check for "Revised Approach" rationale
    if "Revised Approach" not in section_content:
        logger.error("ERROR: 'Revised Approach' text not found in Section 5.")
        is_aligned = False
    else:
        logger.info("INFO: 'Revised Approach' rationale found in Section 5.")

    # 2. Check for "Synthetic Cohort" usage
    # It should ONLY appear in the context of rejection.
    # We check if it appears outside of rejection keywords.
    rejection_keywords = ["Rejection", "Invalid", "Removed", "Deprecated", "Excluded", "Not used", "Rejected"]
    lines = section_content.splitlines()

    found_synthetic = False
    found_in_rejection = False

    for line in lines:
        if "Synthetic Cohort" in line:
            found_synthetic = True
            # Check if any rejection keyword is in the same line or nearby context
            # A simple heuristic: if the line contains rejection keywords, it's likely okay
            # If the line is a positive proposal (e.g., "We will use..."), it's bad.
            if any(kw in line for kw in rejection_keywords):
                found_in_rejection = True
            else:
                # Check surrounding lines for rejection context
                # (Simple check: look at previous 2 lines)
                idx = lines.index(line)
                context = " ".join(lines[max(0, idx-2):idx+1])
                if any(kw in context for kw in rejection_keywords):
                    found_in_rejection = True
                else:
                    logger.error(f"ERROR: 'Synthetic Cohort' found outside of rejection context: {line.strip()}")
                    is_aligned = False

    if found_synthetic and not found_in_rejection:
        logger.error("ERROR: 'Synthetic Cohort' mentioned but not in a rejection context.")
        is_aligned = False
    elif found_synthetic and found_in_rejection:
        logger.info("INFO: 'Synthetic Cohort' mentioned only in rejection context.")
    elif not found_synthetic:
        logger.info("INFO: 'Synthetic Cohort' not mentioned (acceptable if fully removed).")

    return is_aligned

def main():
    """
    Main entry point for verifying Methodological Notes alignment.
    """
    logger = get_logger(__name__)
    logger.info("Starting Methodological Notes Alignment Verification (T074a)...")

    # Determine project root
    project_root = Path(__file__).resolve().parent.parent.parent
    spec_path = project_root / "specs" / "001-social-support-resilience" / "spec.md"

    if not spec_path.exists():
        logger.error(f"ERROR: Spec file not found at {spec_path}")
        sys.exit(1)

    try:
        section_content = find_section_5(spec_path)
        if not section_content:
            logger.error("ERROR: Could not find Section 5 'Methodological Notes' in spec.md")
            sys.exit(1)

        is_aligned = verify_alignment(section_content, logger)

        if is_aligned:
            logger.info("INFO: Methodological Notes verified. Alignment confirmed.")
            # Write success log
            log_path = project_root / "data" / "results" / "methodology_verification.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'w') as f:
                f.write("INFO: Methodological Notes verified. Alignment confirmed.\n")
                f.write("Section 5 contains 'Revised Approach' rationale.\n")
                f.write("'Synthetic Cohort' is handled correctly (rejected/deprecated).\n")
            sys.exit(0)
        else:
            logger.error("ERROR: Methodological Notes mismatch. Manual intervention required.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"ERROR: Verification failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
