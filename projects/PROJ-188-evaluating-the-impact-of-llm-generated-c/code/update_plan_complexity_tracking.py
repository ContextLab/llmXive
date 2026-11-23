"""
T026c: Update plan.md 'Complexity Tracking' section to remove GLMM rationale
and document LMM as the Spec-compliant choice.

This script modifies the project's plan.md file to ensure alignment with
Spec FR-005, which mandates a Linear Mixed Model (LMM) with participant-only
random intercepts, explicitly rejecting the GLMM rationale previously present.
"""
import os
import sys
from pathlib import Path

# Define the path to plan.md relative to the project root
# Assuming this script is run from the project root or code/ directory
def get_plan_path():
    # Try current directory first
    plan_path = Path("plan.md")
    if plan_path.exists():
        return plan_path
    
    # Try parent directory (if running from code/)
    plan_path = Path("../plan.md")
    if plan_path.exists():
        return plan_path
    
    # Try project root directly
    plan_path = Path(__file__).resolve().parent.parent / "plan.md"
    if plan_path.exists():
        return plan_path
        
    raise FileNotFoundError("plan.md not found in expected locations")

def update_plan_content(content: str) -> str:
    """
    Updates the plan.md content to replace GLMM rationale with LMM mandate.
    
    Replacement Text: "Spec FR-005 mandates LMM with participant-only random 
    intercepts; GLMM rejected for non-compliance."
    """
    old_rationale_patterns = [
        "GLMM rationale",
        "Generalized Linear Mixed Model",
        "GLMM",
        "generalized linear mixed model",
        "GLMM approach",
        "GLMM rationale due to binary outcome",
        "GLMM for binary response",
        "GLMM model selection",
        "GLMM is more appropriate",
        "GLMM preferred over LMM",
        "GLMM for this analysis"
    ]
    
    replacement_text = "Spec FR-005 mandates LMM with participant-only random intercepts; GLMM rejected for non-compliance."
    
    updated_content = content
    found_changes = False
    
    # Remove or replace any GLMM rationale mentions
    for pattern in old_rationale_patterns:
        if pattern.lower() in updated_content.lower():
            # Case-insensitive replacement
            import re
            # Create a case-insensitive pattern
            pattern_regex = re.compile(re.escape(pattern), re.IGNORECASE)
            updated_content = pattern_regex.sub(replacement_text, updated_content)
            found_changes = True
    
    # Also look for sections that discuss GLMM vs LMM and replace them
    # Common patterns in scientific writing
    glmm_sections = [
        r"GLMM.*?random intercepts.*?GLMM",
        r"GLMM.*?binary.*?GLMM",
        r"GLMM.*?response.*?GLMM",
        r"GLMM.*?outcome.*?GLMM",
        r"GLMM.*?appropriate.*?GLMM",
        r"GLMM.*?model.*?GLMM"
    ]
    
    for pattern in glmm_sections:
        if re.search(pattern, updated_content, re.IGNORECASE | re.DOTALL):
            updated_content = re.sub(
                pattern, 
                replacement_text, 
                updated_content, 
                flags=re.IGNORECASE | re.DOTALL
            )
            found_changes = True
    
    # If no changes were made, we should at least ensure the correct text exists
    # in the Complexity Tracking section
    if not found_changes:
        # Look for the Complexity Tracking section
        complexity_tracking_marker = "Complexity Tracking"
        if complexity_tracking_marker in updated_content:
            # Find the section and ensure our replacement text is present
            if replacement_text not in updated_content:
                # Add the text after the Complexity Tracking header
                lines = updated_content.split('\n')
                new_lines = []
                for i, line in enumerate(lines):
                    new_lines.append(line)
                    if "Complexity Tracking" in line and i + 1 < len(lines):
                        # Check if next line is a header or content
                        if not lines[i+1].startswith('#') and replacement_text not in lines[i+1]:
                            new_lines.append(replacement_text)
                updated_content = '\n'.join(new_lines)
                found_changes = True
    
    return updated_content, found_changes

def main():
    """Main execution function for T026c."""
    try:
        plan_path = get_plan_path()
        print(f"Found plan.md at: {plan_path}")
        
        # Read current content
        with open(plan_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        print("Original content read successfully.")
        
        # Update content
        updated_content, changes_made = update_plan_content(original_content)
        
        if changes_made:
            # Write updated content back
            with open(plan_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"✅ Successfully updated {plan_path}")
            print("   - Removed GLMM rationale")
            print("   - Added LMM mandate text: 'Spec FR-005 mandates LMM with participant-only random intercepts; GLMM rejected for non-compliance.'")
            return 0
        else:
            # Check if the required text is already present
            required_text = "Spec FR-005 mandates LMM with participant-only random intercepts; GLMM rejected for non-compliance."
            if required_text in original_content:
                print(f"ℹ️  Required text already present in {plan_path}")
                print("   No changes needed.")
                return 0
            else:
                print(f"⚠️  No GLMM rationale found to replace, but required LMM text also missing.")
                print("   Attempting to add the required text to the Complexity Tracking section...")
                
                # Try to add the text anyway
                lines = original_content.split('\n')
                new_lines = []
                added = False
                for i, line in enumerate(lines):
                    new_lines.append(line)
                    if "Complexity Tracking" in line and not added:
                        # Add the required text on the next line if it's not already there
                        if i + 1 < len(lines) and not lines[i+1].startswith('#'):
                            new_lines.append(required_text)
                            added = True
                
                if added:
                    with open(plan_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(new_lines))
                    print(f"✅ Added required text to {plan_path}")
                    return 0
                else:
                    print("❌ Could not locate 'Complexity Tracking' section to add required text.")
                    return 1
                    
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())