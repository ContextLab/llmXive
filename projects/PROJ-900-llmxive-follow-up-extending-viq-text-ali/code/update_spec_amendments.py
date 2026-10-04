"""
T036c: SPEC UPDATE
Edits spec.md to formally document deviations confirmed in T036.
Inserts explicit text blocks into FR-003, FR-004, and SC-004 referencing Decision Record 002.
"""
import os
import sys
import re
from pathlib import Path

def find_spec_file():
    """Locate spec.md in the project root or specs directory."""
    candidates = [
        Path("spec.md"),
        Path("specs/spec.md"),
        Path("specs/001-viq-resolution-invariance/spec.md"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    # Fallback to current directory if not found in standard locations
    spec_path = Path("spec.md")
    if spec_path.exists():
        return spec_path
    raise FileNotFoundError("Could not find spec.md in expected locations.")

def update_spec_content(content: str) -> str:
    """
    Injects required amendment text blocks into FR-003, FR-004, and SC-004.
    
    Targets:
    - FR-003: Add exclusion of ChestX-ray14 per Decision Record 001.
    - FR-004: Add "Native 1024x1024 ground truth used per Decision Record 002".
    - SC-004: Add "Paired t-test or Wilcoxon signed-rank test used per Decision Record 002".
    """
    lines = content.splitlines()
    new_lines = []
    i = 0
    
    # Helper to check if we are in a specific section
    def in_section(section_id):
        return f"{section_id}:" in lines[i] or lines[i].strip().startswith(f"{section_id}")

    while i < len(lines):
        line = lines[i]
        new_lines.append(line)

        # Handle FR-003: Exclusion of ChestX-ray14
        if "FR-003" in line and "Exclusion" not in line:
            # Check if exclusion text is already present
            has_exclusion = False
            for j in range(i, min(i+10, len(lines))):
                if "ChestX-ray14" in lines[j] and "excluded" in lines[j].lower():
                    has_exclusion = True
                    break
            
            if not has_exclusion:
                # Insert exclusion note
                new_lines.append("  > **Amendment**: ChestX-ray14 dataset is explicitly excluded from this study per Decision Record 001.")
        
        # Handle FR-004: Native Ground Truth
        elif "FR-004" in line and "Ground Truth" in line:
            # Check if Decision Record 002 note is present
            has_dr002 = False
            for j in range(i, min(i+10, len(lines))):
                if "Decision Record 002" in lines[j]:
                    has_dr002 = True
                    break
            
            if not has_dr002:
                new_lines.append("  > **Amendment**: Native 1024x1024 ground truth used per Decision Record 002.")

        # Handle SC-004: Paired Test
        elif "SC-004" in line and ("Paired" in line or "t-test" in line or "Wilcoxon" in line):
            # Check if Decision Record 002 note is present
            has_dr002 = False
            for j in range(i, min(i+10, len(lines))):
                if "Decision Record 002" in lines[j]:
                    has_dr002 = True
                    break
            
            if not has_dr002:
                new_lines.append("  > **Amendment**: Paired t-test or Wilcoxon signed-rank test used per Decision Record 002.")

        # Handle SC-004 if it exists but doesn't have the specific keywords yet (fallback)
        elif "SC-004" in line and "Paired" not in line:
            # Check if we need to add the note to the section header or immediately following
            next_lines = lines[i:i+5]
            has_dr002 = any("Decision Record 002" in l for l in next_lines)
            if not has_dr002:
                new_lines.append("  > **Amendment**: Paired t-test or Wilcoxon signed-rank test used per Decision Record 002.")

        i += 1

    return "\n".join(new_lines)

def main():
    spec_path = find_spec_file()
    print(f"Found spec.md at: {spec_path}")

    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        print(f"Error reading spec.md: {e}")
        sys.exit(1)

    updated_content = update_spec_content(original_content)

    if updated_content == original_content:
        print("No changes detected in spec.md. Amendments may already be present.")
        # Still exit 0 as the goal is achieved (content is present)
        sys.exit(0)

    try:
        with open(spec_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Successfully updated {spec_path} with Decision Record 002 amendments.")
        print("Amendments applied:")
        print("  - FR-003: ChestX-ray14 exclusion confirmed.")
        print("  - FR-004: Native 1024x1024 ground truth per Decision Record 002.")
        print("  - SC-004: Paired t-test/Wilcoxon per Decision Record 002.")
    except Exception as e:
        print(f"Error writing to spec.md: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
