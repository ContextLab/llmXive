"""
Task T009c: Update spec.md FR-004 and SC-002.

Replaces:
- "paired-sample t-test" with "one-sample t-test against zero"
- "p < 0.05" with "p < 0.10" for pilot adjustment

Target file: specs/001-examining-the-impact-of-auditory-feedback-motor-learning/spec.md
"""
import sys
from pathlib import Path

def amend_spec():
    spec_path = Path("specs/001-examining-the-impact-of-auditory-feedback-motor-learning/spec.md")
    
    if not spec_path.exists():
        print(f"ERROR: Spec file not found at {spec_path}")
        sys.exit(1)

    original_text = spec_path.read_text()
    
    # Perform replacements
    # 1. Replace paired-sample t-test with one-sample t-test against zero
    amended_text = original_text.replace(
        "paired-sample t-test", 
        "one-sample t-test against zero"
    )
    
    # 2. Replace p < 0.05 with p < 0.10 for pilot adjustment (in FR-004 and SC-002 context)
    # We target the specific phrasing to avoid unintended changes elsewhere
    amended_text = amended_text.replace(
        "p < 0.05 for pilot adjustment",
        "p < 0.10 for pilot adjustment"
    )
    
    # Also handle cases where the phrase might be split or slightly different
    amended_text = amended_text.replace(
        "significance threshold of p < 0.05",
        "significance threshold of p < 0.10"
    )
    
    # Write back if changes were made
    if amended_text != original_text:
        spec_path.write_text(amended_text)
        print(f"Successfully updated {spec_path}")
        print("Changes made:")
        print("  - 'paired-sample t-test' -> 'one-sample t-test against zero'")
        print("  - 'p < 0.05' -> 'p < 0.10' (pilot adjustment context)")
    else:
        print("WARNING: No changes were made. Spec might already be updated or patterns not found.")
        sys.exit(1)

def main():
    amend_spec()

if __name__ == "__main__":
    main()
