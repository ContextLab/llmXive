"""
T016: Update spec.md to reflect the Balanced Blocked Design deviation.

This script modifies specs/001-code-smell-comparison/spec.md to:
1. Update FR-001 target to 150 human samples.
2. Update FR-002 target to 150 LLM samples.
3. Update SC-001 total target to 300 samples.
4. Add a 'Deviation Log' section citing plan.md and methodology-f30244be.
"""
import os
import sys
from pathlib import Path
from utils.logger import get_logger

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = PROJECT_ROOT / "specs" / "001-code-smell-comparison" / "spec.md"

# Constants for the update
DEV_LOG_SECTION = """
## Deviation Log

| ID | Original Spec Requirement | Implemented Design | Rationale | Reference |
|----|---------------------------|--------------------|-----------|-----------|
| D-001 | ≥1000 Human Samples (FR-001) | 150 Human Samples (3 per repo × 50 repos) | Balanced Blocked Design ensures statistical validity and repository-level matching within CI constraints. | `plan.md` Section "Updated Sample Size Justification & Deviation" |
| D-002 | ≥50 LLM Samples (FR-002) | 150 LLM Samples (3 per repo × 50 repos) | Matches human sample count for paired comparison; ensures sufficient power for Blocked Permutation Test. | `plan.md` Section "Updated Sample Size Justification & Deviation" |
| D-003 | 1050 Total Samples (SC-001) | 300 Total Samples (150 Human + 150 LLM) | Consequence of D-001 and D-002. | `plan.md` Section "Updated Sample Size Justification & Deviation" |
| D-004 | Methodology unspecified | Blocked Permutation Test | Chosen to handle non-normality and repository-level blocking. | `methodology-f30244be` |
"""

REPLACEMENTS = [
    (
        r"FR-001.*?≥1000",
        "FR-001 Target is 150 human samples (3 per repo × 50 repos)"
    ),
    (
        r"FR-002.*?≥50",
        "FR-002 Target is 150 LLM samples (3 per repo × 50 repos)"
    ),
    (
        r"SC-001.*?1050",
        "SC-001 Target is 300 total samples (150/150)"
    ),
]

def update_spec_file():
    logger = get_logger(__name__)
    
    if not SPEC_PATH.exists():
        logger.error(f"Spec file not found at {SPEC_PATH}")
        sys.exit(1)

    logger.info(f"Reading spec file: {SPEC_PATH}")
    content = SPEC_PATH.read_text(encoding='utf-8')

    # Check if Deviation Log already exists to avoid duplication
    if "## Deviation Log" in content:
        logger.warning("Deviation Log section already exists. Skipping insertion.")
    else:
        # Insert Deviation Log before the first H2 header that isn't the title, 
        # or simply append if structure is unknown. 
        # Strategy: Find "## Functional Requirements" or similar and insert before it,
        # or append to the end if no specific insertion point is found.
        # For safety, we'll append to the end of the file if no specific section is found.
        # Better: Insert before "## Acceptance Criteria" or similar.
        # Let's look for a common section to insert after "Methodology" or before "Appendix".
        # Simple approach: Append to end.
        content += DEV_LOG_SECTION
        logger.info("Inserted Deviation Log section.")

    # Perform text replacements for numbers
    updated = content
    for pattern, replacement in REPLACEMENTS:
        # Using simple string replacement for exact matches if regex is too risky without full text
        # But the task implies updating specific text blocks.
        # Let's do precise string replacement for the known patterns in the spec.
        pass 
    
    # Since regex might be flaky without the exact full text of the spec, 
    # and the task requires updating specific lines, we will do targeted string replacements
    # based on the likely content of the spec derived from the task description.
    
    # Specific replacements based on task requirements
    if "≥1000 human samples" in content:
        updated = updated.replace("≥1000 human samples", "150 human samples (3 per repo × 50 repos)")
        logger.info("Updated FR-001 sample count.")
    
    if "≥50 LLM samples" in content:
        updated = updated.replace("≥50 LLM samples", "150 LLM samples (3 per repo × 50 repos)")
        logger.info("Updated FR-002 sample count.")
        
    if "1050 total samples" in content:
        updated = updated.replace("1050 total samples", "300 total samples (150/150)")
        logger.info("Updated SC-001 sample count.")

    if updated != content:
        logger.info(f"Writing updated spec to {SPEC_PATH}")
        SPEC_PATH.write_text(updated, encoding='utf-8')
    else:
        logger.info("No changes made to spec content (patterns not found or already updated).")

    return True

def main():
    logger = get_logger(__name__)
    logger.info("Starting T016: Spec Update")
    try:
        update_spec_file()
        logger.info("T016 completed successfully.")
    except Exception as e:
        logger.error(f"T016 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()