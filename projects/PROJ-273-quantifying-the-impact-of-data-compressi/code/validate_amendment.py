"""
validate_amendment.py

This script performs a lightweight, automatic consistency check between the
amendment draft (`amendment_draft.md`) and the implementation plan
(`plan.md`).  It verifies that all functional‑requirement (FR‑###) and
success‑criterion (SC‑###) identifiers referenced in the amendment draft are
also present in the plan.  The result of the check is written to
`data/validation/amendment_validation_report.txt`.

The check is **not** a full manual review – it only flags obvious mismatches
that would indicate the draft is out‑of‑sync with the plan or the
Constitution.  A human reviewer can then inspect the generated report.

The script is deliberately self‑contained and uses only the Python standard
library so it can be executed in the CI environment without additional
dependencies.
"""

import re
import sys
from pathlib import Path
import logging

# Configure a minimal logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _read_file(path: Path) -> str:
    """Read a text file and return its contents."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.error(f"Unable to read {path}: {exc}")
        raise

def _extract_identifiers(text: str, prefix: str) -> set[str]:
    """
    Extract identifiers like ``FR-001`` or ``SC-003`` from ``text``.
    Returns a set of the full identifiers (e.g. ``{'FR-001', 'FR-002'}``).
    """
    pattern = rf"{prefix}-\d{{3}}"
    return set(re.findall(pattern, text))

def _compare_sets(
    draft_set: set[str], plan_set: set[str], label: str
) -> tuple[bool, list[str]]:
    """
    Compare two identifier sets.

    Returns a tuple ``(is_subset, missing)`` where ``missing`` is a list of
    identifiers that appear in the draft but not in the plan.
    """
    missing = sorted(draft_set - plan_set)
    is_subset = len(missing) == 0
    if is_subset:
        logger.info(f"All {label} identifiers from the draft are present in the plan.")
    else:
        logger.warning(
            f"The following {label} identifiers are missing from the plan: {missing}"
        )
    return is_subset, missing

# ----------------------------------------------------------------------
# Main validation routine
# ----------------------------------------------------------------------
def validate_amendment() -> bool:
    """
    Perform the consistency validation.

    Returns ``True`` if the draft is consistent with the plan, ``False``
    otherwise.  A human‑readable report is always written to
    ``data/validation/amendment_validation_report.txt``.
    """
    # Resolve paths relative to the repository root
    repo_root = Path(__file__).resolve().parents[1]

    amendment_path = (
        repo_root
        / "specs"
        / "001-compression-impact-gw-reconstruction"
        / "amendment_draft.md"
    )
    plan_path = (
        repo_root
        / "specs"
        / "001-compression-impact-gw-reconstruction"
        / "plan.md"
    )
    report_path = repo_root / "data" / "validation" / "amendment_validation_report.txt"

    # Ensure the output directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Read files
    amendment_text = _read_file(amendment_path)
    plan_text = _read_file(plan_path)

    # Extract FR and SC identifiers
    fr_draft = _extract_identifiers(amendment_text, "FR")
    sc_draft = _extract_identifiers(amendment_text, "SC")
    fr_plan = _extract_identifiers(plan_text, "FR")
    sc_plan = _extract_identifiers(plan_text, "SC")

    # Perform comparisons
    fr_ok, fr_missing = _compare_sets(fr_draft, fr_plan, "FR")
    sc_ok, sc_missing = _compare_sets(sc_draft, sc_plan, "SC")

    # Assemble report
    lines = [
        "Amendment Draft Validation Report",
        "=================================",
        "",
        f"Draft path: {amendment_path}",
        f"Plan   path: {plan_path}",
        "",
        f"Functional Requirements (FR) found in draft: {sorted(fr_draft)}",
        f"Success Criteria (SC) found in draft: {sorted(sc_draft)}",
        "",
        "Validation Results:",
        "",
    ]

    if fr_ok and sc_ok:
        lines.append("✅ Validation Passed: All FR and SC identifiers from the draft are present in the plan.")
    else:
        lines.append("❌ Validation Failed:")
        if not fr_ok:
            lines.append(
                f"   - Missing FR identifiers in plan: {', '.join(fr_missing) if fr_missing else 'none'}"
            )
        if not sc_ok:
            lines.append(
                f"   - Missing SC identifiers in plan: {', '.join(sc_missing) if sc_missing else 'none'}"
            )
    # Write the report
    report_content = "\n".join(lines) + "\n"
    try:
        report_path.write_text(report_content, encoding="utf-8")
        logger.info(f"Validation report written to {report_path}")
    except Exception as exc:
        logger.error(f"Failed to write report: {exc}")
        raise

    # Return overall success flag
    return fr_ok and sc_ok

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    CLI entry point used by the CI run‑book.  Returns ``0`` on success,
    ``1`` on failure.
    """
    try:
        success = validate_amendment()
        return 0 if success else 1
    except Exception:
        logger.exception("Unexpected error during amendment validation")
        return 1

if __name__ == "__main__":
    sys.exit(main())
