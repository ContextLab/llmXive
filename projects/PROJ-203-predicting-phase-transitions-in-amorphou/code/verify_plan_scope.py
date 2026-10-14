"""Verify that plan.md contains a “Critical Scope Resolution” section
documenting the reduction to 24 compositions.

The script exits with status code 0 if the verification passes.
If the required text is missing, it raises a RuntimeError and exits
with a non‑zero status.
"""
import re
import sys
from llmxive_toolkit import paths

def _load_plan() -> str:
    """Load the contents of plan.md as a string."""
    plan_path = paths.path("plan.md")
    if not plan_path.is_file():
        raise FileNotFoundError(f"plan.md not found at expected location: {plan_path}")
    return plan_path.read_text(encoding="utf-8")

def _verify_critical_scope(plan_text: str) -> bool:
    """Return True if the required section and N=24 text are present."""
    # Check for the heading (case‑insensitive)
    if not re.search(r"Critical\s+Scope\s+Resolution", plan_text, re.IGNORECASE):
        raise RuntimeError(
            "Missing 'Critical Scope Resolution' section in plan.md."
        )
    # Check for a mention of N = 24 (allow spaces around =)
    if not re.search(r"N\s*=\s*24", plan_text):
        raise RuntimeError(
            "The 'Critical Scope Resolution' section does not mention N = 24."
        )
    return True

def main() -> None:
    """Entry point for the verification script."""
    try:
        plan_text = _load_plan()
        _verify_critical_scope(plan_text)
    except Exception as exc:
        # Print the error to stderr for visibility and exit non‑zero
        print(f"Verification failed: {exc}", file=sys.stderr)
        sys.exit(1)
    else:
        # Success
        print("Verification passed: plan.md contains the required section and N = 24.")
        sys.exit(0)

if __name__ == "__main__":
    main()
