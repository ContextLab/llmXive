"""
Task T074a: Verify Methodological Notes Alignment.

Verifies that Section 5 'Methodological Notes' in spec.md:
1. Contains the 'Revised Approach' rationale.
2. Does NOT mention the 'Synthetic Cohort' (except in a rejection context).

This is a verification-only task. It does not modify the spec.
It exits with code 0 on success, or raises RuntimeError on failure.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verify_methodology")

def find_section_5(spec_path: Path) -> str | None:
    """
    Reads the spec.md file and attempts to locate Section 5.
    Returns the content of Section 5 if found, otherwise None.
    """
    if not spec_path.exists():
        logger.error(f"Spec file not found at {spec_path}")
        return None

    try:
        content = spec_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to read spec file: {e}")
        return None

    lines = content.split('\n')
    section_5_start = -1
    section_6_start = -1

    # Look for Section 5 header (e.g., "## 5. Methodological Notes" or "## Section 5")
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#') and '5' in stripped and 'Methodological' in stripped:
            section_5_start = i
        elif section_5_start != -1 and stripped.startswith('#') and ('6' in stripped or 'Section 6' in stripped):
            section_6_start = i
            break

    if section_5_start == -1:
        logger.error("Section 5 'Methodological Notes' not found in spec.md")
        return None

    # Extract section content
    end_idx = section_6_start if section_6_start != -1 else len(lines)
    section_5_content = '\n'.join(lines[section_5_start:end_idx])
    return section_5_content

def verify_alignment(section_content: str) -> tuple[bool, list[str]]:
    """
    Verifies the alignment of the section content.
    Returns (is_aligned, list_of_issues).
    """
    issues = []
    is_aligned = True

    # Check 1: Must contain "Revised Approach"
    if "Revised Approach" not in section_content:
        issues.append("Missing 'Revised Approach' rationale.")
        is_aligned = False
    else:
        logger.info("Found 'Revised Approach' rationale.")

    # Check 2: Must NOT mention "Synthetic Cohort" (unless in a rejection context)
    # We look for the phrase "Synthetic Cohort". If found, we check if it's in a rejection context.
    # A simple heuristic: if "Synthetic Cohort" appears, check if it's preceded by "excluded", "deprecated", "removed", or "invalid".
    # However, the task description says: "does not mention the 'Synthetic Cohort' (except in the rejection context)".
    # To be safe, we will flag if "Synthetic Cohort" is found and not clearly marked as rejected.
    # Given the strictness of the plan, we will treat any mention of "Synthetic Cohort" as a potential issue unless explicitly negated.
    
    if "Synthetic Cohort" in section_content:
        # Check for rejection context keywords nearby
        lines = section_content.split('\n')
        found_rejection = False
        for line in lines:
            if "Synthetic Cohort" in line:
                lower_line = line.lower()
                if any(kw in lower_line for kw in ["excluded", "deprecated", "removed", "invalid", "rejection", "not used", "abandoned"]):
                    found_rejection = True
                    break
        
        if not found_rejection:
            issues.append("Mentions 'Synthetic Cohort' without clear rejection context.")
            is_aligned = False
        else:
            logger.info("Found 'Synthetic Cohort' but it appears to be in a rejection context.")
    else:
        logger.info("No mention of 'Synthetic Cohort' found (aligned).")

    return is_aligned, issues

def main():
    """Main entry point for the verification task."""
    # Determine the path to spec.md relative to the project root
    # Assuming the script is run from the project root or code/ directory
    current_dir = Path.cwd()
    # Try common locations
    possible_paths = [
        current_dir / "specs" / "001-social-support-resilience" / "spec.md",
        current_dir / "specs" / "001-the-impact-of-perceived-social-support-o" / "spec.md",
        current_dir / "project_root" / "specs" / "001-social-support-resilience" / "spec.md",
    ]
    
    spec_path = None
    for p in possible_paths:
        if p.exists():
            spec_path = p
            break

    if spec_path is None:
        # Fallback: look for spec.md in current directory tree
        for root, _, files in os.walk(current_dir):
            if "spec.md" in files:
                candidate = Path(root) / "spec.md"
                # Heuristic: pick the one in a specs directory
                if "specs" in str(candidate):
                    spec_path = candidate
                    break
        
        if spec_path is None:
            logger.error("Could not locate spec.md file.")
            sys.exit(1)

    logger.info(f"Checking spec file at: {spec_path}")
    
    section_content = find_section_5(spec_path)
    if section_content is None:
        logger.error("Failed to extract Section 5.")
        sys.exit(1)

    is_aligned, issues = verify_alignment(section_content)

    if is_aligned:
        logger.info("INFO: Methodological Notes verified.")
        sys.exit(0)
    else:
        logger.error("ERROR: Methodological Notes mismatch.")
        for issue in issues:
            logger.error(f"  - {issue}")
        # Do NOT attempt to edit the spec; just halt.
        sys.exit(1)

if __name__ == "__main__":
    main()
