"""
Task T009d: Spec Update for FR-005.

Updates specs/001-examining-the-impact-of-auditory-feedback-motor-learning/spec.md
to explicitly state "global learning rate slope (independent of condition)" in FR-005.
"""
import sys
from pathlib import Path

def amend_spec():
    """
    Reads the spec file, finds FR-005, and updates the learning rate definition
    to be explicitly global and independent of condition.
    """
    spec_path = Path("specs/001-examining-the-impact-of-auditory-feedback-motor-learning/spec.md")
    
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec file not found at {spec_path}")
    
    content = spec_path.read_text()
    
    # Define the target update for FR-005
    # We look for the FR-005 section and ensure the specific phrasing is present.
    # The task requires explicitly stating "global learning rate slope (independent of condition)".
    
    target_phrase = "global learning rate slope (independent of condition)"
    
    # Check if the phrase already exists to avoid redundant edits
    if target_phrase in content:
        print(f"FR-005 already contains the required phrase: '{target_phrase}'")
        return True

    # Strategy: Locate FR-005 and update the description of the learning rate metric.
    # We assume the spec follows a standard format where FR-005 is a block.
    # We will replace generic "learning rate" references in the FR-005 block with the specific definition.
    
    lines = content.split('\n')
    new_lines = []
    in_fr005 = False
    updated = False

    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # Detect start of FR-005
        if line.strip().startswith("## FR-005") or line.strip().startswith("### FR-005"):
            in_fr005 = True
            continue
        
        # Detect end of FR-005 (next FR or End of Section)
        if in_fr005 and (line.strip().startswith("## FR-") or line.strip().startswith("### FR-") or line.strip().startswith("---")):
            in_fr005 = False
        
        if in_fr005 and not updated:
            # Look for the definition of the learning rate metric in this section
            # Common patterns: "Metric: learning rate", "The learning rate is...", "We calculate the learning rate..."
            if "learning rate" in line.lower() and "slope" not in line.lower():
                # Attempt to inject the clarification
                # We replace the generic phrase with the specific one if it looks like a definition
                if "calculate" in line.lower() or "defined" in line.lower() or "metric" in line.lower():
                    # Insert the clarification after the mention of learning rate
                    # Example: "The learning rate is calculated..." -> "The global learning rate slope (independent of condition) is calculated..."
                    new_line = line.replace("learning rate", target_phrase, 1)
                    new_lines[-1] = new_line
                    updated = True
                    print(f"Updated line {i+1} in FR-005 to use: '{target_phrase}'")
        
        # Fallback: If we are in FR-005 and haven't found a specific line to edit, 
        # but we reach the end of the block, we might need to insert a sentence.
        # However, the above heuristic is safer for in-place replacement.
    
    if not updated:
        # If we couldn't find a specific line to edit, we append a clarification note at the end of the FR-005 block
        # We need to find where FR-005 ended or is ending
        # Re-scan to find the end of FR-005 block logic
        pass

    # If the simple replacement didn't work, we perform a more robust regex-based replacement
    # for the specific requirement if it's missing.
    if target_phrase not in content:
        # We will try to find the FR-005 header and inject the text if not found
        # This is a fallback for cases where the line structure is complex
        import re
        
        # Pattern to match FR-005 block (assuming headers are ## or ###)
        # We will look for the header and then the next few lines
        pattern = r"(## FR-005.*?)(?=\n## FR-|\n### FR-|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            fr005_block = match.group(1)
            if "global learning rate" not in fr005_block:
                # Inject a sentence clarifying the metric
                injection = "\n\n**Metric Definition**: The learning rate is defined as the **global learning rate slope (independent of condition)**."
                new_block = fr005_block + injection
                content = content.replace(fr005_block, new_block)
                updated = True
                print("Injected clarification into FR-005 block.")
        else:
            # Fallback: Just append to the end of the file if FR-005 is not found (should not happen)
            print("Warning: Could not locate FR-005 block to update.")
            return False

    # Write the updated content
    spec_path.write_text(content)
    print(f"Successfully updated {spec_path} for Task T009d.")
    return True

def main():
    try:
        success = amend_spec()
        if success:
            print("T009d: Spec update completed successfully.")
            sys.exit(0)
        else:
            print("T009d: Spec update failed to locate target section.")
            sys.exit(1)
    except Exception as e:
        print(f"T009d: Error during spec update: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
