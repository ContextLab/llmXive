"""
Governance (SCR) Implementation: Update spec.md to reflect the exclusion of FR-008 (Weapons).

This module implements Task T020c by:
1. Removing FR-008 from the Functional Requirements list in spec.md.
2. Updating User Story 2 (US-2) to reflect the exclusion of "weapons" and focus solely on "Face" ROIs.
"""
import os
import sys
import logging
import re
from pathlib import Path
from typing import List, Tuple

# Add project root to path to allow imports from sibling modules if needed
# Assuming this script is run from the project root or code/scr/
# We rely on the standard project structure where 'code' is at the root relative to this script if run from code/
# But since we are writing a file, we just need to handle the text manipulation.

from utils.logging import get_logger, setup_logging
from utils.versioning import register_artifact

# Setup logging
logger = get_logger(__name__)

def remove_fr_008(content: str) -> str:
    """
    Removes the FR-008 entry from the Functional Requirements section.
    
    Assumes FR-008 is formatted as a list item starting with 'FR-008' or similar.
    We look for the specific pattern of the weapons exclusion requirement.
    """
    lines = content.split('\n')
    new_lines = []
    skip_next = False
    in_func_reqs = False

    # Pattern to identify the start of the Functional Requirements section (optional, for context)
    # We look for lines that define FR-008 specifically.
    
    for i, line in enumerate(lines):
        # Check if we are entering the Functional Requirements section (heuristic)
        if '## Functional Requirements' in line or 'Functional Requirements' in line:
            in_func_reqs = True
        
        # Heuristic to detect FR-008 line. Usually starts with FR-008 or - FR-008
        if re.match(r'^\s*[-*]?\s*FR-008\b', line, re.IGNORECASE):
            logger.info(f"Removing FR-008 line: {line.strip()}")
            skip_next = True
            continue
        
        # If we are skipping, we might need to skip the next line if it's a continuation or description
        # Typically in these docs, the requirement is one line or a block.
        # Let's assume it's a single line item for now, but if the next line is indented and part of the description, skip it too.
        if skip_next:
            if line.strip() == "" or not line.startswith(' ' * 4) and not line.startswith('\t'):
                # If the next line is not a continuation (not indented) or is a new top-level item, stop skipping
                skip_next = False
            else:
                # It's a continuation, skip it
                logger.info(f"Removing FR-008 continuation: {line.strip()}")
                continue
        
        new_lines.append(line)

    return '\n'.join(new_lines)

def update_user_story_2(content: str) -> str:
    """
    Updates User Story 2 to reflect the exclusion of 'weapons' and focus on 'Face' ROIs.
    
    Specifically looks for references to "weapons" in the context of US-2 or the eye-tracking 
    analysis section and updates them to reflect the SCR decision.
    """
    lines = content.split('\n')
    new_lines = []
    in_us2 = False
    
    for line in lines:
        # Detect start of User Story 2
        if '## User Story 2' in line or 'User Story 2:' in line or 'US-2' in line:
            in_us2 = True
        
        # Detect end of US-2 (start of US-3 or next major section)
        if in_us2 and ('## User Story 3' in line or '## User Story 3' in line):
            in_us2 = False
        
        if in_us2:
            # Update specific references
            # Replace "weapons" exclusion logic if it was previously mentioned as a pending task or included
            # The task is to update the story to REFLECT the exclusion.
            # If the text says "Analyze weapons and faces", change to "Analyze faces (weapons excluded per SCR)".
            
            if 'weapons' in line.lower():
                # If it's part of a requirement that is now removed, we might need to be careful.
                # However, the task is to update the story to reflect the exclusion.
                # If the text says "including weapons", we remove that part.
                if 'including weapons' in line.lower():
                    line = line.lower().replace('including weapons', '(weapons excluded per SCR)').replace('including weapons', '(weapons excluded per SCR)').title() # Preserve case roughly
                elif 'and weapons' in line.lower():
                    line = line.lower().replace(' and weapons', ' (weapons excluded per SCR)').title()
                elif 'weapons' in line.lower() and 'exclude' not in line.lower():
                    # If it mentions weapons without excluding them, update to reflect exclusion
                    # e.g., "Process weapons and faces" -> "Process faces (weapons excluded)"
                    line = line.replace('weapons', 'faces (weapons excluded per SCR)')
            
            # Ensure the focus is on Face ROIs
            if 'ROI' in line and 'face' not in line.lower() and 'weapons' not in line.lower():
                # If it's generic, maybe clarify? No, only change if it mentions weapons.
                pass

        new_lines.append(line)

    return '\n'.join(new_lines)

def main():
    """
    Main execution function for T020c.
    """
    setup_logging()
    logger.info("Starting T020c: Update spec.md to remove FR-008 and update US-2")

    # Determine paths
    # Assuming project root is the parent of 'code'
    project_root = Path(__file__).resolve().parent.parent
    spec_path = project_root / "specs" / "spec.md"
    
    if not spec_path.exists():
        # Try alternative location if specs are at root
        spec_path = project_root / "spec.md"
    
    if not spec_path.exists():
        logger.error("spec.md not found in expected locations.")
        raise FileNotFoundError("spec.md not found.")

    logger.info(f"Reading spec file: {spec_path}")
    with open(spec_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Step 1: Remove FR-008
    logger.info("Removing FR-008 from Functional Requirements...")
    updated_content = remove_fr_008(content)

    # Step 2: Update User Story 2
    logger.info("Updating User Story 2 to reflect weapons exclusion...")
    updated_content = update_user_story_2(updated_content)

    # Write back
    logger.info(f"Writing updated spec file: {spec_path}")
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    # Register artifact for versioning
    register_artifact(spec_path)

    logger.info("T020c completed successfully.")

if __name__ == "__main__":
    main()