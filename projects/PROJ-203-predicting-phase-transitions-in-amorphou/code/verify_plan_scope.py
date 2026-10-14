"""
verify_plan_scope.py

Checks that `plan.md` contains a “Critical Scope Resolution” section and that the
section explicitly mentions the pilot size N = 24. Exits with status 0 if both
conditions are met, otherwise prints an error message and exits with status 1.
"""

import sys
import re
from pathlib import Path

def main() -> None:
    # Resolve the project root (assumes this script lives in <project>/code/)
    project_root = Path(__file__).resolve().parent.parent
    plan_path = project_root / "plan.md"

    if not plan_path.is_file():
        print(f"ERROR: plan.md not found at expected location: {plan_path}", file=sys.stderr)
        sys.exit(1)

    try:
        content = plan_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"ERROR: Could not read plan.md: {e}", file=sys.stderr)
        sys.exit(1)

    # Condition 1: Presence of the Critical Scope Resolution heading/paragraph
    if not re.search(r"Critical\s+Scope\s+Resolution", content, re.IGNORECASE):
        print("ERROR: 'Critical Scope Resolution' section not found in plan.md", file=sys.stderr)
        sys.exit(1)

    # Condition 2: Explicit mention of the pilot size N = 24 (allow spaces around =)
    if not re.search(r"N\s*=\s*24", content):
        print("ERROR: Pilot size 'N = 24' not mentioned in the Critical Scope Resolution section", file=sys.stderr)
        sys.exit(1)

    # All checks passed
    print("plan.md verification passed: Critical Scope Resolution present and N = 24 documented.")
    sys.exit(0)

if __name__ == "__main__":
    main()