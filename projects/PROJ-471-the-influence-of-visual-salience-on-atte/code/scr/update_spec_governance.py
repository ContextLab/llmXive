import os
import sys
import logging
import re
from pathlib import Path
from typing import List, Tuple

from utils.logging import get_logger

logger = get_logger(__name__)

def load_file(path: Path) -> str:
    """Load file contents."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding="utf-8")

def save_file(path: Path, content: str) -> None:
    """Save content to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info(f"Saved file: {path}")

def remove_fr_008_from_spec(content: str) -> str:
    """
    Remove FR-008 (Weapons) from Functional Requirements in spec.md.
    Also updates the list to ensure consistency.
    """
    # Pattern to match FR-008 line and potentially the list item
    # Looking for lines like: "- **FR-008**: ..." or "- [ ] FR-008 ..."
    pattern = r"-+\s*\[?[xX ]?\]?\s*FR-008.*?(?=\n-|\Z)"
    
    # More robust: Find the section "Functional Requirements" and remove the specific item
    # We look for the line starting with FR-008
    lines = content.split('\n')
    new_lines = []
    in_requirements = False
    found_fr008 = False

    for line in lines:
        stripped = line.strip()
        
        # Detect start of Functional Requirements section
        if "Functional Requirements" in line or "FR-" in line and "##" in line:
            in_requirements = True
            new_lines.append(line)
            continue

        # If we are in requirements and find FR-008
        if in_requirements and "FR-008" in line:
            logger.info(f"Removing FR-008 line: {line.strip()}")
            found_fr008 = True
            continue  # Skip this line

        # If we hit a new major section (##), stop looking for FR-008 in this block
        if in_requirements and line.startswith("##") and "Functional Requirements" not in line:
            in_requirements = False

        new_lines.append(line)

    if not found_fr008:
        logger.warning("FR-008 was not found in the spec content.")
    
    return '\n'.join(new_lines)

def update_user_story_2(content: str) -> str:
    """
    Update User Story 2 to reflect "Face" ROIs only and mention SCR-001 exclusion.
    """
    # Update the description of US2 to explicitly mention Face only and weapons exclusion
    old_us2_desc = "extract fixation metrics for \"Face\" ROIs (excluding \"weapons\" due to SCR-001)"
    new_us2_desc = "extract fixation metrics for \"Face\" ROIs only (Weapons excluded per SCR-001)"
    
    if old_us2_desc in content:
        content = content.replace(old_us2_desc, new_us2_desc)
        logger.info("Updated User Story 2 description.")
    else:
        # Fallback: try to find the section and update the context
        # Look for the US2 header and ensure the text mentions Face only
        lines = content.split('\n')
        new_lines = []
        in_us2 = False
        
        for line in lines:
            if "## User Story 2" in line or "US2" in line and "Attention" in line:
                in_us2 = True
                new_lines.append(line)
                continue
            
            if in_us2 and "Weapons" in line and "excluded" not in line.lower():
                # Add a note about exclusion if not already present
                if "SCR-001" not in line:
                    line = line + " (Weapons excluded per SCR-001)"
            
            if in_us2 and line.startswith("##") and "User Story" not in line:
                in_us2 = False
            
            new_lines.append(line)
        
        content = '\n'.join(new_lines)

    return content

def update_plan_md(content: str) -> str:
    """
    Update plan.md to explicitly state FR-008 is excluded.
    """
    # Check if exclusion is already noted
    if "FR-008" in content and "excluded" in content.lower():
        logger.info("FR-008 exclusion already noted in plan.md.")
        return content

    # Add a note in the Notes or Dependencies section
    # Find the "Notes" section or add one at the end
    lines = content.split('\n')
    new_lines = []
    found_notes = False
    exclusion_note = "\n- **Spec Gap**: \"Weapons\" (FR-008) excluded; only \"Face\" ROIs implemented (see T020a-c, SCR-001)."

    for i, line in enumerate(lines):
        new_lines.append(line)
        if "## Notes" in line:
            found_notes = True
            # Insert note immediately after the header or next line
            if i + 1 < len(lines) and not lines[i+1].startswith("-"):
                new_lines.append(exclusion_note)
            elif i + 1 < len(lines) and "FR-008" not in lines[i+1]:
                new_lines.append(exclusion_note)
    
    if not found_notes:
        new_lines.append("\n## Notes")
        new_lines.append(exclusion_note)

    return '\n'.join(new_lines)

def main():
    """
    Main entry point for T020c: Apply SCR-001 to spec.md and plan.md.
    """
    root = Path(__file__).resolve().parent.parent.parent
    spec_path = root / "spec.md"
    plan_path = root / "plan.md"

    logger.info(f"Starting SCR-001 Apply (T020c) for project root: {root}")

    if not spec_path.exists():
        logger.error(f"spec.md not found at {spec_path}")
        sys.exit(1)
    if not plan_path.exists():
        logger.error(f"plan.md not found at {plan_path}")
        sys.exit(1)

    # Process spec.md
    spec_content = load_file(spec_path)
    spec_content = remove_fr_008_from_spec(spec_content)
    spec_content = update_user_story_2(spec_content)
    save_file(spec_path, spec_content)

    # Process plan.md
    plan_content = load_file(plan_path)
    plan_content = update_plan_md(plan_content)
    save_file(plan_path, plan_content)

    logger.info("T020c completed successfully: FR-008 removed from spec and plan updated.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main()