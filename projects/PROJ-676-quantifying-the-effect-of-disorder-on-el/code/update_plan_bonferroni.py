"""
T015a (Part 2): Update Plan Artifact for Bonferroni Correction

Edits plan.md to replace "Bonferroni correction for pairwise comparisons only"
with "Bonferroni correction for the full family of disorder widths".
"""
import re
from pathlib import Path

PLAN_FILE = Path(__file__).parent.parent / "plan.md"

def main():
    if not PLAN_FILE.exists():
        raise FileNotFoundError(f"Plan file not found: {PLAN_FILE}")

    content = PLAN_FILE.read_text()

    # Target string to replace
    old_phrase = "Bonferroni correction for pairwise comparisons only"
    new_phrase = "Bonferroni correction for the full family of disorder widths"

    if old_phrase not in content:
        print(f"Warning: '{old_phrase}' not found in {PLAN_FILE}. "
              "The plan may have already been updated or uses different phrasing.")
        # Check if the new phrase is already there
        if new_phrase in content:
            print("The new phrase is already present. No changes made.")
            return 0
        else:
            # If neither is found, we cannot proceed safely without knowing the exact context.
            # However, per task description, we assume it exists.
            # We will raise an error to fail loudly as per constraints.
            raise ValueError(
                f"Could not find the target phrase '{old_phrase}' in {PLAN_FILE}. "
                "Cannot perform the update. Please verify the plan content."
            )

    # Perform replacement
    new_content = content.replace(old_phrase, new_phrase)

    # Write back
    PLAN_FILE.write_text(new_content)

    print(f"Successfully updated {PLAN_FILE}:")
    print(f"  '{old_phrase}' -> '{new_phrase}'")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())