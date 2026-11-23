import os
import sys
import logging
import re
from pathlib import Path
from typing import List, Tuple, Optional

from utils.logging import get_logger

logger = get_logger(__name__)

def load_file(file_path: Path) -> str:
    """Load the contents of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def save_file(file_path: Path, content: str) -> None:
    """Save content to a file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"Saved file: {file_path}")

def remove_fr_009_from_spec(spec_content: str) -> str:
    """
    Remove FR-009 from the Functional Requirements list in spec.md content.
    Looks for lines starting with 'FR-009' or containing 'FR-009' in a list item.
    """
    lines = spec_content.split('\n')
    new_lines = []
    found = False
    for line in lines:
        # Match lines that define FR-009, e.g., "- [ ] FR-009 ..." or "FR-009: ..."
        if re.match(r'^\s*[-*]\s*\[?\s*[xX]?\s*]??\s*FR-009\b', line):
            logger.info(f"Removing FR-009 from spec: {line.strip()}")
            found = True
            continue
        # Also match if FR-009 is part of a description that should be removed entirely
        # This is a heuristic; adjust if spec format varies significantly
        if 'FR-009' in line and re.search(r'FR-009\s*[:\s]', line):
             # If it's not a list item but a header or definition line
             if re.match(r'^\s*FR-009\b', line):
                 logger.info(f"Removing FR-009 header/def from spec: {line.strip()}")
                 found = True
                 continue

        new_lines.append(line)

    if not found:
        logger.warning("FR-009 was not found in the spec content. It may have already been removed or formatted differently.")
    else:
        logger.info("Successfully removed FR-009 references from spec content.")

    return '\n'.join(new_lines)

def update_plan_md_for_fr009(plan_content: str) -> str:
    """
    Update plan.md to explicitly state FR-009 is excluded.
    Adds a note in the 'Notes' or 'Governance' section if it doesn't exist,
    or updates an existing note about FR-009.
    """
    exclusion_note = (
        "\n- **Spec Contradiction**: Low-level covariates (FR-009) excluded to prevent multicollinearity with DeepGaze II "
        "(see T030c-e, SCR-002)."
    )

    # Check if the note already exists
    if "FR-009" in plan_content and "excluded" in plan_content.lower():
        logger.info("FR-009 exclusion note already present in plan.md.")
        return plan_content

    # Try to append to a 'Notes' section if one exists
    if '\n## Notes' in plan_content:
        # Append after the last line of the Notes section (simplified: append before next section or end)
        # A safer approach is to just append to the end if we can't find a clean insertion point
        plan_content += exclusion_note
        logger.info("Appended FR-009 exclusion note to plan.md Notes section.")
    else:
        # If no Notes section, append to the end of the file
        plan_content += "\n\n## Notes\n" + exclusion_note
        logger.info("Added Notes section and FR-009 exclusion note to plan.md.")

    return plan_content

def main() -> None:
    """
    Main entry point to apply SCR-002: Remove FR-009 from spec.md and update plan.md.
    """
    root_dir = Path(__file__).resolve().parents[2]
    spec_path = root_dir / "spec.md"
    plan_path = root_dir / "plan.md"

    if not spec_path.exists():
        logger.error(f"spec.md not found at {spec_path}")
        sys.exit(1)
    if not plan_path.exists():
        logger.error(f"plan.md not found at {plan_path}")
        sys.exit(1)

    try:
        # Load files
        spec_content = load_file(spec_path)
        plan_content = load_file(plan_path)

        # Process spec.md
        updated_spec = remove_fr_009_from_spec(spec_content)

        # Process plan.md
        updated_plan = update_plan_md_for_fr009(plan_content)

        # Save files
        save_file(spec_path, updated_spec)
        save_file(plan_path, updated_plan)

        logger.info("SCR-002 (FR-009 exclusion) successfully applied to spec.md and plan.md.")

    except Exception as e:
        logger.error(f"Failed to apply SCR-002: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
