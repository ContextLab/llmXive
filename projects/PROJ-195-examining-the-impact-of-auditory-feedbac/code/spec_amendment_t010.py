"""
Task T010: Spec Amendment - Update FR-004 statistical method.

Replaces "paired-sample t-test" with "one-sample t-test against zero"
in FR-004 of spec.md.
"""
import sys
from pathlib import Path

def amend_spec():
    """Update spec.md FR-004 text."""
    spec_path = Path("specs/001-examining-the-impact-of-auditory-feedback-motor-learning/spec.md")
    
    if not spec_path.exists():
        print(f"ERROR: spec.md not found at {spec_path}")
        sys.exit(1)
    
    content = spec_path.read_text()
    
    # Perform the exact text replacement required
    old_text = "paired-sample t-test"
    new_text = "one-sample t-test against zero"
    
    if old_text not in content:
        print(f"WARNING: '{old_text}' not found in spec.md. No changes made.")
        return False
    
    updated_content = content.replace(old_text, new_text)
    
    # Verify the replacement happened in FR-004 context
    # We look for the specific context to ensure we updated the right place
    if new_text in updated_content:
        spec_path.write_text(updated_content)
        print(f"SUCCESS: Updated FR-004 in {spec_path}")
        print(f"  Replaced: '{old_text}' -> '{new_text}'")
        return True
    else:
        print("ERROR: Replacement did not take effect.")
        return False

def main():
    success = amend_spec()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()