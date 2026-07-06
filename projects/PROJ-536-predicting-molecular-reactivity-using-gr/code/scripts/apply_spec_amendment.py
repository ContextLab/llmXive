"""
Script to apply a spec amendment request to the main specification file.
This script updates spec.md by replacing the content of a specific Functional Requirement.
"""
import os
import sys
import yaml
from datetime import datetime

# Add project root to path if not already present
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def check_amendment_file_exists(amendment_path: str) -> bool:
    """
    Checks if the specified amendment file exists.
    
    Args:
        amendment_path: Relative path to the amendment markdown file.
        
    Returns:
        True if file exists, False otherwise.
    """
    full_path = os.path.join(project_root, amendment_path)
    return os.path.isfile(full_path)

def update_spec_markdown(spec_path: str, amendment_path: str, fr_id: str) -> bool:
    """
    Updates the spec.md file by replacing the content of a specific Functional Requirement.
    
    This function:
    1. Reads the amendment file to extract the new requirement text.
    2. Reads the current spec.md.
    3. Locates the section for the specified FR_ID.
    4. Replaces the old content with the new content from the amendment.
    5. Writes the updated content back to spec.md.
    
    Args:
        spec_path: Relative path to spec.md.
        amendment_path: Relative path to the amendment markdown file.
        fr_id: The ID of the Functional Requirement to update (e.g., "FR-008").
        
    Returns:
        True if update was successful, False otherwise.
    """
    spec_full_path = os.path.join(project_root, spec_path)
    amendment_full_path = os.path.join(project_root, amendment_path)

    if not os.path.isfile(spec_full_path):
        print(f"Error: Spec file not found at {spec_full_path}")
        return False

    if not os.path.isfile(amendment_full_path):
        print(f"Error: Amendment file not found at {amendment_full_path}")
        return False

    try:
        # Read the amendment content
        with open(amendment_full_path, 'r', encoding='utf-8') as f:
            amendment_content = f.read()

        # Extract the new requirement text from the amendment.
        # We assume the amendment has a "Proposed Change" section or similar structure.
        # For this specific task, we look for the block starting with "> **FR-008**" or similar.
        # To be robust, we will look for the section defined in the amendment.
        
        # Simple heuristic: Look for the section starting with "> **FR-008" and ending before the next "##" or end of file.
        # However, since we are replacing a specific block, let's assume the amendment file contains the exact replacement text
        # in a structured way. For this implementation, we will parse the "Proposed Change" section.
        
        lines = amendment_content.split('\n')
        new_fr_text = []
        in_proposed_change = False
        
        for line in lines:
            if "## Proposed Change" in line:
                in_proposed_change = True
                continue
            if in_proposed_change:
                if line.strip().startswith("## "):
                    break
                new_fr_text.append(line)
        
        if not new_fr_text:
            print("Error: Could not extract new requirement text from amendment.")
            return False

        new_fr_block = '\n'.join(new_fr_text).strip()

        # Read the current spec
        with open(spec_full_path, 'r', encoding='utf-8') as f:
            spec_content = f.read()

        # We need to find the block in spec.md that corresponds to FR-008.
        # Since the structure of spec.md is markdown, we will use a regex or line-by-line approach.
        # We assume the spec.md has a section like "**FR-008:** ..." or similar.
        # Given the constraints, we will perform a string replacement if the exact old header is found.
        
        # Heuristic: Find the line starting with the FR_ID and replace until the next FR_ID or end of section.
        # This is a simplified approach. A more robust parser would be needed for complex specs.
        
        # Let's assume the spec.md has a structure:
        # **FR-008: Old Text**
        # ...
        
        # We will search for the start marker.
        start_marker = f"**{fr_id}:"
        end_marker = f"**{fr_id.split('-')[0]}-{int(fr_id.split('-')[1]) + 1:03d}:" # Next FR ID, e.g., FR-009

        if start_marker not in spec_content:
            print(f"Error: Could not find {fr_id} in spec.md to replace.")
            return False

        # Find start index
        start_idx = spec_content.find(start_marker)
        
        # Find end index (next FR or end of file)
        end_idx = len(spec_content)
        if end_marker in spec_content:
            end_idx = spec_content.find(end_marker)
        
        # Extract the old block
        old_block = spec_content[start_idx:end_idx]
        
        # Replace
        updated_content = spec_content.replace(old_block, new_fr_block, 1)

        # Write back
        with open(spec_full_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"Successfully updated {fr_id} in {spec_path}")
        return True

    except Exception as e:
        print(f"Error updating spec: {e}")
        return False

def main():
    """
    Main entry point to apply the FR-008 amendment.
    """
    amendment_file = "specs/001-predicting-molecular-reactivity-using-gr/amendments/FR-008-scaffold-split-amendment.md"
    spec_file = "specs/001-predicting-molecular-reactivity-using-gr/spec.md"
    fr_id = "FR-008"

    if not check_amendment_file_exists(amendment_file):
        print(f"Amendment file not found: {amendment_file}")
        sys.exit(1)

    success = update_spec_markdown(spec_file, amendment_file, fr_id)
    
    if success:
        print("Amendment applied successfully.")
        sys.exit(0)
    else:
        print("Failed to apply amendment.")
        sys.exit(1)

if __name__ == "__main__":
    main()