"""
Spec Alignment Verification Module.

This module verifies that spec.md and plan.md are consistent regarding
the statistical method (Maximum Statistic) before implementation begins.
"""
import os
import sys
from pathlib import Path
from typing import Tuple, List, Optional

# Constants for verification
REQUIRED_METHOD = "Maximum Statistic"
FORBIDDEN_METHOD = "Benjamini-Hochberg"
US3_SECTION_KEYWORD = "US3"
STAT_METHOD_KEYWORD = "Statistical Method"


def load_file_text(file_path: str) -> str:
    """
    Load text content from a file.

    Args:
        file_path: Path to the file.

    Returns:
        String content of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def check_spec_alignment(spec_content: str, plan_content: str) -> Tuple[bool, List[str], str]:
    """
    Verify alignment between spec.md and plan.md regarding the statistical method.

    Args:
        spec_content: Content of spec.md.
        plan_content: Content of plan.md.

    Returns:
        Tuple of (is_aligned, list_of_issues, summary_message).
    """
    issues = []
    is_aligned = True
    summary_msg = ""

    # 1. Check spec.md for US3 and Statistical Method sections
    spec_has_max_stat = REQUIRED_METHOD.lower() in spec_content.lower()
    spec_forbids_bh = FORBIDDEN_METHOD.lower() + " is NOT used" in spec_content.lower() or \
                      "NOT used" in spec_content and FORBIDDEN_METHOD.lower() in spec_content.lower()

    # Check for explicit mention of US3
    spec_has_us3 = US3_SECTION_KEYWORD.lower() in spec_content.lower()

    if not spec_has_max_stat:
        issues.append(f"CRITICAL: Spec does not explicitly mention '{REQUIRED_METHOD}'.")
        is_aligned = False
    elif not spec_forbids_bh:
        # Check if it implies BH is used
        if FORBIDDEN_METHOD.lower() in spec_content.lower() and "used" in spec_content.lower():
            if "is NOT used" not in spec_content.lower():
                issues.append(f"WARNING: Spec mentions '{FORBIDDEN_METHOD}' but does not explicitly state it is NOT used.")
        else:
             issues.append(f"WARNING: Spec does not explicitly state '{FORBIDDEN_METHOD} is NOT used'.")

    if not spec_has_us3:
        issues.append("WARNING: Spec does not explicitly mention US3 section.")

    # 2. Check plan.md Summary and Technical Context
    plan_has_max_stat = REQUIRED_METHOD.lower() in plan_content.lower()
    plan_impl_max_stat = "maximum statistic" in plan_content.lower() or "max statistic" in plan_content.lower()

    if not plan_has_max_stat and not plan_impl_max_stat:
        issues.append(f"CRITICAL: Plan does not implement '{REQUIRED_METHOD}'.")
        is_aligned = False

    # 3. Check Plan's "Note on Spec Conflict"
    # Look for text claiming Spec mandates BH
    plan_text = plan_content.lower()
    spec_text = spec_content.lower()

    # Check if Plan claims Spec mandates BH
    # This is a heuristic check for the specific error mentioned in the task
    conflict_note_present = "note on spec conflict" in plan_text or "spec conflict" in plan_text
    plan_claims_spec_mandates_bh = False

    if conflict_note_present:
        # Look for patterns like "Spec mandates BH" or "Spec requires BH"
        if "spec mandates" in plan_text and FORBIDDEN_METHOD.lower() in plan_text:
            plan_claims_spec_mandates_bh = True
        elif "spec requires" in plan_text and FORBIDDEN_METHOD.lower() in plan_text:
            plan_claims_spec_mandates_bh = True

    if plan_claims_spec_mandates_bh:
        issues.append("DOCUMENTATION ERROR: Plan's 'Note on Spec Conflict' incorrectly claims Spec mandates BH.")
        # This is a documentation error, not necessarily a method mismatch if the plan implements Max Stat
        if plan_impl_max_stat:
            summary_msg = "Spec and Plan both mandate Maximum Statistic. Plan's 'Note on Spec Conflict' is a documentation error."
        else:
            is_aligned = False
            summary_msg = "Plan claims Spec mandates BH, but Plan implements neither Max Stat nor BH correctly."
    else:
        # No false claim found
        if plan_impl_max_stat:
            summary_msg = "Spec and Plan are ALIGNED on Maximum Statistic."
        else:
            is_aligned = False
            summary_msg = "Plan does not implement Maximum Statistic."

    # 4. Final Resolution
    if is_aligned:
        if "DOCUMENTATION ERROR" in "\n".join(issues):
            summary_msg = "Spec Alignment Verified: Spec and Plan both mandate Maximum Statistic. Plan's 'Note on Spec Conflict' is flagged as a documentation error (incorrectly claims Spec mandates BH)."
        else:
            summary_msg = "Spec Alignment Verified: Spec and Plan are consistent on Maximum Statistic."
    else:
        summary_msg = "Spec/Plan Mismatch: Statistical Method Conflict detected."

    return is_aligned, issues, summary_msg


def main():
    """
    Main entry point for spec alignment verification.
    """
    # Define paths relative to project root
    # Assuming this script runs from code/ or project root
    project_root = Path(__file__).resolve().parent.parent
    spec_path = project_root / "specs" / "001-assessing-the-validity-of-the-cosmologic" / "spec.md"
    plan_path = project_root / "plan.md"
    output_dir = project_root / "data" / "reports"
    output_file = output_dir / "spec_alignment_log.txt"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load files
        spec_content = load_file_text(str(spec_path))
        plan_content = load_file_text(str(plan_path))

        # Check alignment
        is_aligned, issues, summary_msg = check_spec_alignment(spec_content, plan_content)

        # Generate report
        report_lines = [
            "=" * 60,
            "SPEC ALIGNMENT VERIFICATION REPORT",
            "=" * 60,
            f"Status: {'PASSED' if is_aligned else 'FAILED'}",
            f"Timestamp: {os.popen('date').read().strip()}",
            "-" * 60,
            "Summary:",
            summary_msg,
            "-" * 60,
            "Issues/Notes:",
        ]
        if issues:
            for i, issue in enumerate(issues, 1):
                report_lines.append(f"{i}. {issue}")
        else:
            report_lines.append("No issues found.")

        report_lines.append("=" * 60)

        report_text = "\n".join(report_lines)

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)

        print(report_text)

        if not is_aligned:
            print("\nCRITICAL: Spec/Plan Mismatch detected. Halting further tasks.")
            sys.exit(1)
        else:
            print("\nSpec Alignment Verified. Implementation tasks may proceed.")
            sys.exit(0)

    except FileNotFoundError as e:
        error_msg = f"File Not Found: {e}"
        print(error_msg)
        # Write error to log
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"ERROR: {error_msg}\n")
        sys.exit(1)
    except Exception as e:
        error_msg = f"Unexpected Error: {e}"
        print(error_msg)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"ERROR: {error_msg}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
