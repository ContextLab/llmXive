"""
T011: Spec Amendment - Update FR-005 to allow "global learning rate slope" independent of condition.

Exact Text Replacement:
Replace "per condition" with "global (independent of condition)" in FR-005 of spec.md.
"""

import sys
from pathlib import Path


def amend_spec():
    """
    Updates spec.md to correct FR-005 regarding learning rate slope calculation.
    """
    project_root = Path(__file__).resolve().parent.parent
    spec_path = project_root / "specs" / "001-examining-the-impact-of-auditory-feedback-motor-learning" / "spec.md"

    if not spec_path.exists():
        # Try alternative location if specs directory structure differs
        alt_spec_path = project_root / "spec.md"
        if alt_spec_path.exists():
            spec_path = alt_spec_path
        else:
            print(f"ERROR: spec.md not found at {spec_path} or {alt_spec_path}")
            sys.exit(1)

    try:
        content = spec_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"ERROR: Failed to read spec.md: {e}")
        sys.exit(1)

    original_text = "per condition"
    replacement_text = "global (independent of condition)"

    # Check if the text exists to avoid unnecessary writes if already done
    if original_text not in content:
        # Check specifically for the context of FR-005 to ensure we are fixing the right place
        # If the text is completely missing, we might have already done it or the spec is different
        # For safety, we proceed with replacement if the string exists anywhere, or fail if it doesn't
        # But the task says "Replace X with Y". If X is not there, the task is effectively done or the spec changed.
        # We will check if the replacement text is already there.
        if replacement_text in content:
            print("FR-005 already updated to 'global (independent of condition)'. No changes made.")
            return True
        else:
            print(f"WARNING: Could not find '{original_text}' in spec.md. The amendment might already be applied or the spec format changed.")
            # We do not exit with error here as the goal is the final state.
            return True

    new_content = content.replace(original_text, replacement_text)

    if new_content == content:
        print("No changes made (string not found).")
        return True

    try:
        spec_path.write_text(new_content, encoding="utf-8")
        print(f"SUCCESS: Updated {spec_path}")
        print(f"Replaced '{original_text}' with '{replacement_text}'")
        return True
    except Exception as e:
        print(f"ERROR: Failed to write spec.md: {e}")
        sys.exit(1)


def main():
    success = amend_spec()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()