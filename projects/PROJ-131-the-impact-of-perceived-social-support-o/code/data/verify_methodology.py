import os
import sys
import logging
from pathlib import Path
import json

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger

def find_section_5(file_path: Path) -> str:
    """
    Reads the spec file and extracts the content of Section 5 (Methodological Notes).
    Returns the raw text of the section or an empty string if not found.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Spec file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    section_start = -1
    section_end = len(lines)

    # Heuristic: Find line starting with "## Methodological Notes" or "## 5. Methodological Notes"
    for i, line in enumerate(lines):
        if line.strip().startswith("## Methodological Notes") or (line.strip().startswith("## 5.") and "Methodological Notes" in line):
            section_start = i
            break

    if section_start == -1:
        return ""

    # Find the next section (##) to determine the end of Section 5
    for i in range(section_start + 1, len(lines)):
        if lines[i].strip().startswith("## ") and not lines[i].strip().startswith("###"):
            section_end = i
            break

    return '\n'.join(lines[section_start:section_end])

def verify_alignment(section_text: str) -> dict:
    """
    Verifies that Section 5 contains the 'Revised Approach' text
    and that 'Synthetic Cohort' is mentioned ONLY in the context of rejection.
    """
    result = {
        "aligned": True,
        "issues": [],
        "has_revised_approach": False,
        "has_synthetic_cohort": False,
        "synthetic_cohort_in_rejection_context": True
    }

    if not section_text:
        result["aligned"] = False
        result["issues"].append("Section 5 not found or empty.")
        return result

    # Check for "Revised Approach"
    if "Revised Approach" in section_text or "single-dataset" in section_text.lower():
        result["has_revised_approach"] = True
    else:
        result["has_revised_approach"] = False
        result["issues"].append("Missing 'Revised Approach' or 'single-dataset' rationale.")
        result["aligned"] = False

    # Check for "Synthetic Cohort"
    if "Synthetic Cohort" in section_text:
        result["has_synthetic_cohort"] = True
        # Check if it appears in a rejection context
        # Look for patterns like "rejected", "invalid", "removed", "deprecated" near the phrase
        lines = section_text.split('\n')
        valid_context_found = False
        for line in lines:
            if "Synthetic Cohort" in line:
                lower_line = line.lower()
                if any(keyword in lower_line for keyword in ["rejected", "invalid", "removed", "deprecated", "excluded", "not used"]):
                    valid_context_found = True
                    break
        
        if not valid_context_found:
            result["synthetic_cohort_in_rejection_context"] = False
            result["issues"].append("'Synthetic Cohort' found but not clearly in a rejection context.")
            result["aligned"] = False
    else:
        # If not found at all, that's also acceptable per the spec (it might be completely removed)
        # But the task says "mentioned ONLY in the context of rejection", so absence is fine if Revised Approach is there.
        pass

    return result

def main():
    logger = get_logger(__name__)
    spec_path = Path("specs/001-social-support-resilience/spec.md")

    if not spec_path.exists():
        logger.error(f"Spec file not found at {spec_path}")
        sys.exit(1)

    logger.info(f"Verifying alignment for {spec_path}")
    section_text = find_section_5(spec_path)
    alignment_result = verify_alignment(section_text)

    # Log results
    if alignment_result["aligned"]:
        logger.info("INFO: Methodological Notes verified.")
        logger.info("Spec is aligned with the Plan's Revised Approach.")
        sys.exit(0)
    else:
        logger.error("ERROR: Methodological Notes mismatch.")
        for issue in alignment_result["issues"]:
            logger.error(f"  - {issue}")
        logger.error("Triggering T074b (Repair) to update the spec.")
        # We do not exit with error code here because the task description implies
        # that if verification fails, we should trigger the repair logic.
        # However, for a standalone script, we usually exit 1 on failure.
        # The pipeline orchestration will catch this and run the repair.
        sys.exit(1)

if __name__ == "__main__":
    main()
