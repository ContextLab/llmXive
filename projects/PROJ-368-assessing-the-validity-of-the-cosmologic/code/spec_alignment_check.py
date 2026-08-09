"""
Task T001: Spec Alignment Verification.

Verifies that spec.md and plan.md are consistent regarding the statistical method.
Specifically checks for "Maximum Statistic approach" and absence of "Benjamini-Hochberg".

Output:
- data/reports/spec_alignment_log.txt: "Spec Alignment Verified" on success.
- Raises ValueError with specific message on failure.
"""
import os
import sys
from pathlib import Path

# Ensure we can import from the code directory
CODE_ROOT = Path(__file__).parent
PROJECT_ROOT = CODE_ROOT.parent
DATA_REPORTS_DIR = PROJECT_ROOT / "data" / "reports"

# Paths to check
SPEC_PATH = PROJECT_ROOT / "specs" / "001-assessing-the-validity-of-the-cosmologic" / "spec.md"
PLAN_PATH = PROJECT_ROOT / "specs" / "001-assessing-the-validity-of-the-cosmologic" / "plan.md"
OUTPUT_LOG = DATA_REPORTS_DIR / "spec_alignment_log.txt"

def load_file_text(filepath: Path) -> str:
    if not filepath.exists():
        raise FileNotFoundError(f"Required file not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def check_spec_alignment():
    """
    Performs the verification logic for T001.
    """
    # Ensure output directory exists
    DATA_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load files
    try:
        spec_content = load_file_text(SPEC_PATH)
        plan_content = load_file_text(PLAN_PATH)
    except FileNotFoundError as e:
        # If files are missing, we cannot verify alignment.
        # This is a failure state for the task.
        print(f"CRITICAL: {e}")
        raise

    # 1. Check spec.md for "Maximum Statistic approach"
    # We look for the specific phrase required by the task description.
    has_max_stat = "Maximum Statistic approach" in spec_content
    
    # 2. Check spec.md for absence of "Benjamini-Hochberg"
    # The task requires that this correction is NOT used/stated.
    has_bh = "Benjamini-Hochberg" in spec_content

    # 3. Check plan.md for the "Note on Spec Conflict" context if it exists,
    # but primarily we rely on the spec being corrected.
    # The task says: "Compare with plan.md 'Note on Spec Conflict'".
    # If the plan mentions a conflict, we ensure the spec is now aligned.
    plan_has_conflict_note = "Note on Spec Conflict" in plan_content or "Statistical Method Conflict" in plan_content

    # Decision Logic
    is_aligned = has_max_stat and not has_bh

    if not is_aligned:
        reason = []
        if not has_max_stat:
            reason.append("spec.md missing 'Maximum Statistic approach'")
        if has_bh:
            reason.append("spec.md still contains 'Benjamini-Hochberg'")
        
        error_msg = "Spec/Plan Mismatch: Statistical Method Conflict. " + "; ".join(reason)
        print(f"ERROR: {error_msg}")
        # Write failure log to ensure the file exists with the error state
        with open(OUTPUT_LOG, 'w', encoding='utf-8') as f:
            f.write(f"VERIFICATION FAILED: {error_msg}\n")
        raise ValueError(error_msg)

    # If aligned, write success log
    log_content = "Spec Alignment Verified\n"
    log_content += f"Checked: {SPEC_PATH.name}\n"
    log_content += f"Verified: 'Maximum Statistic approach' present\n"
    log_content += f"Verified: 'Benjamini-Hochberg' absent\n"
    
    with open(OUTPUT_LOG, 'w', encoding='utf-8') as f:
        f.write(log_content)
    
    print("SUCCESS: Spec Alignment Verified. Output written to:", OUTPUT_LOG)
    return True

if __name__ == "__main__":
    try:
        check_spec_alignment()
    except (FileNotFoundError, ValueError) as e:
        # Re-raise to signal failure clearly
        sys.exit(1)
