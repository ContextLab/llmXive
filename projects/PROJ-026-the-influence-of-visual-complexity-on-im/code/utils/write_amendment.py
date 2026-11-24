"""
T000: Create Amendment 001 (ANOVA -> Permutation Test) and update the
project state file's updated_at timestamp.

Writes specs/001-the-influence-of-visual-complexity-on-im/amendment-001.md
with the ratified text (date = execution date) and ensures
state/projects/PROJ-026-the-influence-of-visual-complexity-on-im.yaml
exists with updated_at set to the current timestamp.
"""
from datetime import datetime, timezone
from pathlib import Path

from llmxive_toolkit import paths

AMENDMENT_TEXT = """# Amendment 001: Replacement of FR-003

**Date**: {date}
**Status**: Ratified

## Summary
This amendment replaces the original Functional Requirement FR-003 (Repeated-Measures ANOVA) with a **Permutation Test** (n=1000) to assess the significance of the difference in D-scores between complexity conditions.

## Justification
The original ANOVA requirement is methodologically invalid because 'Stimulus Set' is perfectly confounded with 'Complexity Level'. A parametric ANOVA would violate the assumption of independence. A Permutation Test provides a non-parametric alternative that correctly handles the stimulus-set confound by randomizing labels within the observed data structure.

## Impact
- **FR-003**: Updated to require Permutation Test.
- **Code**: `code/analysis/permutation.py` must implement the new logic.
- **Spec**: `spec.md` updated to reference this amendment.
"""

def main() -> None:
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Write the amendment file
    amendment_path = paths.path(
        "specs", "001-the-influence-of-visual-complexity-on-im",
        "amendment-001.md",
    )
    amendment_path.parent.mkdir(parents=True, exist_ok=True)
    amendment_path.write_text(AMENDMENT_TEXT.format(date=date_str), encoding="utf-8")
    print(f"Wrote {amendment_path}")

    # Verify ratification marker
    content = amendment_path.read_text(encoding="utf-8")
    assert "Status: Ratified" in content, "Ratified status line missing!"

    # 2. Create / update the project state file
    state_path = paths.path(
        "state", "projects",
        "PROJ-026-the-influence-of-visual-complexity-on-im.yaml",
    )
    state_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    if state_path.exists():
        lines = state_path.read_text(encoding="utf-8").splitlines()
        lines = [ln for ln in lines if not ln.startswith("updated_at:")]
    else:
        lines = [
            "project_id: PROJ-026-the-influence-of-visual-complexity-on-im",
            "title: The Influence of Visual Complexity on Implicit Bias",
            "status: active",
        ]

    lines.append(f"updated_at: {timestamp}")
    state_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Updated {state_path} (updated_at: {timestamp})")

if __name__ == "__main__":
    main()