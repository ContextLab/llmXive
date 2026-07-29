"""
Script to fix the formula description in plan.md.
This script updates the Constitution Check section under Principle VII
to correct the formula from L_phys = (R_Earth) / Vsw_mean to
L_phys = 6371 / Vsw_mean, explicitly stating the distance is 60 R_E.
"""
import os
import re
from pathlib import Path

def fix_plan_formula():
    """Fix the formula in plan.md."""
    plan_path = Path("specs/PROJ-300-01-solar-wind-reconnection/plan.md")
    
    if not plan_path.exists():
        print(f"Error: {plan_path} does not exist.")
        return False
    
    with open(plan_path, 'r') as f:
        content = f.read()
    
    # Find and replace the incorrect formula description
    # Look for the pattern that describes the formula incorrectly
    old_pattern = r"L_phys = \(R_Earth\) / Vsw_mean"
    new_text = "L_phys = 6371 / Vsw_mean (derived from 60 * 6371 / 60, where 60 R_E is the tail distance)"
    
    # Check if the old pattern exists
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_text, content)
        print("Found and replaced incorrect formula description.")
    else:
        # Try a more flexible pattern matching
        flexible_pattern = r"L_phys\s*=\s*\(?\s*R_Earth\s*\)?\s*/\s*Vsw_mean"
        if re.search(flexible_pattern, content):
            content = re.sub(flexible_pattern, new_text, content)
            print("Found and replaced incorrect formula description (flexible pattern).")
        else:
            print("Warning: Could not find the exact formula pattern to replace.")
            print("Manual review of plan.md may be required.")
            return False
    
    # Also ensure the text explicitly states the distance is 60 R_E
    if "60 R_E" not in content and "60 Re" not in content:
        # Add clarification about the distance
        clarification = " (the distance is 60 R_E)"
        # Find the section about L_phys and add clarification
        if "L_phys" in content:
            content = content.replace("L_phys = 6371 / Vsw_mean", f"L_phys = 6371 / Vsw_mean{clarification}")
            print("Added clarification about 60 R_E distance.")
    
    # Write the updated content back
    with open(plan_path, 'w') as f:
        f.write(content)
    
    print(f"Successfully updated {plan_path}")
    return True

if __name__ == "__main__":
    fix_plan_formula()
