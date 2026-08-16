"""
Plan Updater for PROJ-509.

This script updates the plan.md file to explicitly include the required artifacts
in the "Single Source of Truth" section as per task T026a.

Artifacts to include:
- permutation_importance.json
- feature_ranking.json
- vif_scores.json
"""
import re
from pathlib import Path

def update_plan():
    """Update plan.md to include new artifacts in the Single Source of Truth section."""
    plan_path = Path("plan.md")
    if not plan_path.exists():
        print("Error: plan.md not found in project root.")
        return False

    content = plan_path.read_text()
    
    # Define the new artifacts to add
    new_artifacts = [
        "- `data/evaluation/permutation_importance.json`",
        "- `data/evaluation/feature_ranking.json`",
        "- `data/evaluation/vif_scores.json`"
    ]
    
    # Find the "Single Source of Truth" section
    # We look for the section header and the list of artifacts below it
    sso_pattern = r"(Single Source of Truth.*?)(\n## |\n### |\Z)"
    match = re.search(sso_pattern, content, re.DOTALL | re.IGNORECASE)
    
    if not match:
        print("Warning: 'Single Source of Truth' section not found. Attempting to append at end.")
        # Fallback: append to end
        content += "\n## Single Source of Truth\n\n"
        for artifact in new_artifacts:
            content += f"{artifact}\n"
        plan_path.write_text(content)
        print("Updated plan.md with new artifacts (appended).")
        return True

    section_text = match.group(1)
    remainder = match.group(2)
    
    # Check if artifacts are already present
    artifacts_present = all(any(artifact in section_text for artifact in new_artifacts))
    
    if artifacts_present:
        print("All required artifacts are already listed in the 'Single Source of Truth' section.")
        return True
    
    # Find the list of artifacts in the section
    # Look for a bulleted list pattern
    list_pattern = r"(- `data/evaluation/model_metrics.json`.*?)(?=\n-|\n## |\n### |\Z)"
    list_match = re.search(list_pattern, section_text, re.DOTALL)
    
    if list_match:
        existing_list = list_match.group(1)
        # Append new artifacts to the existing list
        updated_list = existing_list
        for artifact in new_artifacts:
            if artifact not in existing_list:
                updated_list += f"\n{artifact}"
        
        # Replace the old list with the new one
        new_section_text = section_text.replace(existing_list, updated_list)
        new_content = content.replace(section_text + remainder, new_section_text + remainder)
        plan_path.write_text(new_content)
        print("Updated plan.md with new artifacts in 'Single Source of Truth' section.")
        return True
    else:
        # No existing list found, try to add after the section header
        header_pattern = r"(Single Source of Truth)"
        header_match = re.search(header_pattern, section_text, re.IGNORECASE)
        if header_match:
            insert_pos = header_match.end()
            # Find the end of the line
            while insert_pos < len(section_text) and section_text[insert_pos] not in ['\n', '\r']:
                insert_pos += 1
            if insert_pos < len(section_text) and section_text[insert_pos] == '\n':
                insert_pos += 1
            
            new_artifacts_text = "\n" + "\n".join(new_artifacts) + "\n"
            new_section_text = section_text[:insert_pos] + new_artifacts_text + section_text[insert_pos:]
            new_content = content.replace(section_text + remainder, new_section_text + remainder)
            plan_path.write_text(new_content)
            print("Updated plan.md with new artifacts in 'Single Source of Truth' section.")
            return True
    
    print("Could not locate appropriate insertion point in 'Single Source of Truth' section.")
    return False

if __name__ == "__main__":
    success = update_plan()
    if not success:
        exit(1)
    print("Plan update completed successfully.")
