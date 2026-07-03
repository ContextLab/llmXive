"""
Task T000b: Align plan.md with the amended spec.md.

This script reads the existing plan.md, updates the Summary section to reflect
the N=30 prompt scope (10 CodeXGLUE + 20 handcrafted) and N=90 snippets,
and ensures consistency with the resource constraints documented in spec.md.

It writes the updated content to a new plan.md file.
"""
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PLAN_FILE = PROJECT_ROOT / "plan.md"

# The specific text block to replace or insert in the Summary section.
# We look for the "## Summary" section and update the first paragraph.
AMENDED_SCOPE_TEXT = """The project scope has been amended to address resource constraints (GitHub Actions 7GB RAM, 6h execution limit).
The dataset size is reduced to **N=30 prompts** (10 from CodeXGLUE + 20 handcrafted), resulting in **N=90 code snippets** (3 models x 30 prompts).
This ensures the pipeline can complete within the allocated CI resources while maintaining statistical validity for the primary research questions."""

def align_plan():
    if not PLAN_FILE.exists():
        raise FileNotFoundError(f"plan.md not found at {PLAN_FILE}")

    content = PLAN_FILE.read_text()

    # Check if the summary section exists
    if "## Summary" not in content:
        raise ValueError("plan.md does not contain a '## Summary' section.")

    # Strategy: Find the Summary section and replace the first paragraph after the header
    # or append the amendment if the section is empty.
    
    # Split by headers to find the summary block
    lines = content.split('\n')
    new_lines = []
    in_summary = False
    summary_updated = False

    for i, line in enumerate(lines):
        if line.strip().startswith("## Summary"):
            new_lines.append(line)
            in_summary = True
            # Check if the next line is a paragraph or just whitespace
            # We will inject our text if it's the first non-empty line after the header
            continue
        
        if in_summary and not summary_updated:
            # If we hit a new section, we failed to update (shouldn't happen if structure is correct)
            if line.strip().startswith("## "):
                in_summary = False
                # If we reach here without updating, we append before the next header
                new_lines.append(f"\n{AMENDED_SCOPE_TEXT}")
                summary_updated = True
            
            # If the current line is empty or just whitespace, skip it to find the first content
            # Actually, we want to insert the amendment right after the header, 
            # or replace the existing summary paragraph if it looks like the old one.
            # Let's assume the first non-empty line after "## Summary" is the old summary.
            if line.strip() == "":
                new_lines.append(line)
                continue
            
            # If we are here, we found the first content line of the summary.
            # We will replace it with our amended text block.
            new_lines.append(AMENDED_SCOPE_TEXT)
            new_lines.append("") # Add a blank line after
            summary_updated = True
            in_summary = False # Stop looking for the first line
            continue
        
        new_lines.append(line)

    if not summary_updated:
        # Fallback: Append to the end of the file if logic failed
        new_lines.append("\n## Summary (Amended)")
        new_lines.append(AMENDED_SCOPE_TEXT)

    updated_content = "\n".join(new_lines)
    
    # Write back to plan.md
    PLAN_FILE.write_text(updated_content)
    print(f"Successfully updated {PLAN_FILE} with N=30 scope alignment.")

if __name__ == "__main__":
    align_plan()