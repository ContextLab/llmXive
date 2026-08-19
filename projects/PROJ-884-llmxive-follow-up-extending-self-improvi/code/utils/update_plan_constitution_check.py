"""
Script to update plan.md Constitution Check table for Principle VII.
This script modifies the plan.md file to reflect the 'PARTIALLY SATISFIED' status
of Principle VII due to the impossibility of empirical GPU calibration on CPU runners.
"""
import os
import re
from pathlib import Path

def update_plan_constitution_check():
    plan_path = Path("plan.md")
    if not plan_path.exists():
        # If plan.md doesn't exist in the expected location, try to find it or exit gracefully
        # In a real scenario, we might search or raise an error, but for this task
        # we assume it exists or we just log the intended change.
        print("Warning: plan.md not found. Skipping update.")
        return

    content = plan_path.read_text()
    
    # Pattern to find the Principle VII section in the Constitution Check table
    # We look for a line containing "Principle VII" and update its status.
    # Assuming a markdown table format like: | Principle VII | ... | [ ] SATISFIED |
    
    # Regex to find the line with Principle VII and capture the status column
    # Adjust regex based on actual markdown table structure if needed.
    # Example pattern for a markdown table row:
    pattern = r"(\|.*Principle VII.*\|).*\|.*\[(.*?)\].*\|"
    
    new_content = content
    
    # Check if we can find and update the line
    if re.search(pattern, content, re.IGNORECASE):
        # Replace the status bracket content
        # If it was [ ] SATISFIED or [x] SATISFIED, change to [ ] PARTIALLY SATISFIED
        new_content = re.sub(
            r"(\|.*Principle VII.*\|.*\[)[xX ](.*?)(\].*)",
            r"\1 \3", # Remove the checkmark
            content,
            flags=re.IGNORECASE
        )
        
        # Now we need to specifically set the text to "PARTIALLY SATISFIED"
        # This is a bit tricky with regex in one pass, so we do a targeted replace
        # Find the line with Principle VII and replace the status text
        lines = new_content.split('\n')
        updated = False
        for i, line in enumerate(lines):
            if "Principle VII" in line and "PARTIALLY SATISFIED" not in line:
                # Replace any existing status with PARTIALLY SATISFIED
                # Assuming the status is in the last column or a specific column
                # We'll do a simple replace of common status markers
                if "[ ] SATISFIED" in line:
                    lines[i] = line.replace("[ ] SATISFIED", "[ ] PARTIALLY SATISFIED")
                    updated = True
                elif "[x] SATISFIED" in line:
                    lines[i] = line.replace("[x] SATISFIED", "[ ] PARTIALLY SATISFIED")
                    updated = True
                elif "SATISFIED" in line and "PARTIALLY" not in line:
                    # If it's just the word SATISFIED without brackets, adjust accordingly
                    lines[i] = line.replace("SATISFIED", "PARTIALLY SATISFIED")
                    updated = True
        
        if updated:
            new_content = '\n'.join(lines)
            plan_path.write_text(new_content)
            print("Updated plan.md: Principle VII set to PARTIALLY SATISFIED")
        else:
            print("Could not find a standard status marker for Principle VII to update.")
    else:
        print("Could not locate Principle VII in plan.md. Manual update required.")
        print("Please ensure the Constitution Check table in plan.md includes Principle VII.")

def main():
    update_plan_constitution_check()

if __name__ == "__main__":
    main()