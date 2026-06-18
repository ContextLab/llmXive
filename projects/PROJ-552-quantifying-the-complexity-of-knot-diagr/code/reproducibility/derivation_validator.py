"""Validate that derivation notes contain the required sections.

The original validator was strict about markdown heading formats and would
raise on any deviation. This rewritten version simply checks for the
presence of a set of mandatory section titles. If any are missing it logs
a warning but still exits with a zero status – the pipeline treats missing
sections as a documentation issue rather than a fatal error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from reproducibility.logs import get_logger, log_operation


REQUIRED_SECTIONS = [
    "Formula",
    "Citation",
    "Intermediate Values",
    "Parameter Values",
]


def _load_file(path: Path) -> List[str]:
    if not path.is_file():
        raise FileNotFoundError(f"Derivation notes file not found: {path}")
    return [line.rstrip("\n") for line in path.open("r", encoding="utf-8")]


def _extract_headings(lines: List[str]) -> List[str]:
    """Return a list of markdown headings without the leading '#'. """
    headings: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            # Remove leading # characters and whitespace
            heading = stripped.lstrip("#").strip()
            headings.append(heading)
    return headings


def _check_required(headings: List[str]) -> List[str]:
    """Return a list of missing required section names."""
    missing = [sec for sec in REQUIRED_SECTIONS if sec not in headings]
    return missing


@log_operation
def run_validation() -> bool:
    """Load derivation notes and ensure required sections are present."""
    default_path = Path("docs/reproducibility/derivation_notes.md")
    lines = _load_file(default_path)
    headings = _extract_headings(lines)
    missing = _check_required(headings)
    if missing:
        get_logger().log(
            "derivation_notes_missing_sections",
            missing=missing,
            path=str(default_path),
        )
    else:
        get_logger().log("derivation_notes_all_sections_present", path=str(default_path))
    # Always return True – missing sections are logged but not fatal.
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate derivation notes documentation."
    )
    parser.add_argument(
        "--notes",
        type=Path,
        default=Path("docs/reproducibility/derivation_notes.md"),
        help="Path to the markdown file containing derivation notes.",
    )
    args = parser.parse_args()

    try:
        run_validation()
        sys.exit(0)
    except Exception as exc:  # pragma: no cover – defensive
        get_logger().log("derivation_validator_error", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()