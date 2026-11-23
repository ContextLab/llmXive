import os
import sys
import re
from pathlib import Path

def update_plan_file(plan_path: str = "plan.md") -> None:
    """
    Updates plan.md to align with Spec FR-001 regarding method counts.
    
    Changes:
    1. Removes references to '100 methods'.
    2. Ensures 'Max a reasonable number of methods per repository to ensure manageability and coherence.' is present in Performance Goals/Constraints.
    3. Ensures total count is described as up to 20,000 (20 repos * [deferred]).
    4. Removes the 'Note' suggesting fallback to 8-bit/full precision if 4-bit fails.
    """
    path = Path(plan_path)
    if not path.exists():
        raise FileNotFoundError(f"Plan file not found at {plan_path}")

    content = path.read_text(encoding='utf-8')
    original_content = content

    # 1. Remove references to '100 methods' (case insensitive, flexible spacing)
    # Matches "100 methods", "100  methods", "100 methods per repo", etc.
    content = re.sub(r'\b100\s+methods\b', '[deferred] methods', content, flags=re.IGNORECASE)
    
    # 2. Remove the specific fallback note regarding 8-bit/full precision
    # Pattern to match the note about fallback
    fallback_note_pattern = r"Note.*?fallback to 8-bit.*?precision.*?\n"
    content = re.sub(fallback_note_pattern, "", content, flags=re.DOTALL | re.IGNORECASE)
    # Also try a single line version if the note is compact
    fallback_note_pattern_single = r"Note.*?fallback to 8-bit.*?precision.*"
    content = re.sub(fallback_note_pattern_single, "", content, flags=re.IGNORECASE)

    # 3. Ensure the hard cap statement exists in Performance Goals or Constraints
    # We look for a section header and ensure the text follows or is present nearby.
    # If the specific text is missing, we insert it near the "Constraints" or "Performance Goals" section.
    target_text = "Max a reasonable number of methods per repository to ensure manageability and coherence."
    
    if target_text not in content:
        # Attempt to insert after "## Constraints" or "## Performance Goals"
        # We look for "Constraints" first, then "Performance Goals"
        insert_marker = None
        if "## Constraints" in content:
            insert_marker = "## Constraints"
        elif "## Performance Goals" in content:
            insert_marker = "## Performance Goals"
        else:
            # Fallback: append to end of file if sections not found (should not happen in a proper plan)
            # But for safety, we'll just prepend a note at the top if we can't find a section
            content = f"### Constraints\n{target_text}\n\n" + content
        
        if insert_marker:
            # Insert the line after the header
            lines = content.split('\n')
            new_lines = []
            inserted = False
            for line in lines:
                new_lines.append(line)
                if not inserted and line.strip() == insert_marker:
                    new_lines.append(target_text)
                    inserted = True
            content = '\n'.join(new_lines)

    # 4. Ensure the total count description is present (up to 20,000)
    # We ensure a statement like "up to 20,000 (20 repos * [deferred])" exists.
    count_text = "up to 20,000 (20 repos * [deferred])"
    if count_text not in content:
        # Try to add it near the method cap text we just added or near a "Total" mention
        if target_text in content:
            content = content.replace(target_text, f"{target_text} Total count is {count_text}.")
        else:
            # Fallback insertion
            content = f"Total dataset size is {count_text}.\n" + content

    if content == original_content:
        print(f"Plan file at {plan_path} appears to already be aligned or no changes were necessary.")
    else:
        path.write_text(content, encoding='utf-8')
        print(f"Successfully updated {plan_path}.")

def main():
    """Entry point for the plan updater script."""
    plan_file = "plan.md"
    if len(sys.argv) > 1:
        plan_file = sys.argv[1]
    
    try:
        update_plan_file(plan_file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error updating plan: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
