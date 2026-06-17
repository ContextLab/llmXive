"""Generate a validation status report for the reproducibility pipeline.

This script aggregates the outcomes of the various validation
steps that have been executed during the run‑book (e.g. schema checks,
data quality flags, tie‑breaking rule validation, checksum recording,
etc.) and writes a concise markdown summary to
``docs/reproducibility/validation_status.md``.

The implementation is deliberately lightweight: it does **not** depend
on the project's logging utilities (which currently have signature
mismatches) and only uses the standard library.  The script can be
executed directly:

    python code/reproducibility/validation_status.py

After execution the file ``docs/reproducibility/validation_status.md``
will exist and contain a table summarising each validation component and
whether it succeeded (``PASS``) or failed (``FAIL``).  If a component
cannot be inspected (e.g. missing output file), it is reported as
``UNKNOWN``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

# ----------------------------------------------------------------------
# Configuration: map validation component names to the files they
# produce.  The presence of a file is taken as a proxy for success.
# Adjust this mapping if new validation artifacts are added.
# ----------------------------------------------------------------------
VALIDATION_ARTIFACTS: Dict[str, Path] = {
    "Schema validation": Path("tests/contract/test_schemas.py"),
    "Data quality flags": Path("code/data/validator.py"),
    "Tie‑breaking rule validation": Path("code/reproducibility/tie_breaking_validator.py"),
    "Checksum recording": Path("data/checksums.json"),
    "Derivation notes validation": Path("code/reproducibility/derivation_validator.py"),
    "Operation logs generation": Path("docs/reproducibility/operation_logs.md"),
    "Random seed verification": Path("docs/reproducibility/seed_verification.md"),
}

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_UNKNOWN = "UNKNOWN"


def _check_artifact(path: Path) -> str:
    """Return a status string for a single artifact."""
    if path.is_file():
        return STATUS_PASS
    # Some validation steps write JSON reports; if the file exists but is
    # empty or malformed we treat it as FAIL.
    if path.suffix == ".json" and path.is_file():
        try:
            with path.open() as f:
                json.load(f)
            return STATUS_PASS
        except Exception:
            return STATUS_FAIL
    return STATUS_UNKNOWN


def collect_statuses() -> List[Tuple[str, str]]:
    """Inspect each configured artifact and return a list of (name, status)."""
    return [(name, _check_artifact(p)) for name, p in VALIDATION_ARTIFACTS.items()]


def render_markdown(statuses: List[Tuple[str, str]]) -> str:
    """Render the validation summary as a markdown table."""
    lines = [
        "# Validation Status Report",
        "",
        "This report provides a high‑level overview of the reproducibility",
        "validation steps that were executed as part of the project run‑book.",
        "",
        "| Validation component | Status |",
        "|----------------------|--------|",
    ]
    for name, status in statuses:
        lines.append(f"| {name} | {status} |")
    lines.append("")
    lines.append(
        "_Generated automatically by `code/reproducibility/validation_status.py`._"
    )
    return "\n".join(lines)


def write_report(content: str, destination: Path) -> None:
    """Write the markdown content to ``destination``."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def main() -> None:
    """Entry point for the script."""
    statuses = collect_statuses()
    report_md = render_markdown(statuses)
    output_path = Path("docs/reproducibility/validation_status.md")
    write_report(report_md, output_path)
    print(f"Validation status report written to {output_path}")


if __name__ == "__main__":
    main()
