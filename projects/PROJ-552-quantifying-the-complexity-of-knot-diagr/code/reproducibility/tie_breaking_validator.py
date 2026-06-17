"""
Tie-breaking Rule Consistency Validator
---------------------------------------

This script validates that the tie-breaking rules documented in
``docs/reproducibility/tie_breaking_rules.md`` follow a simple
consistency contract:

* Every rule must be expressed as a bullet point (``-`` or ``*``).
* The bullet must be followed by non‑empty text.
* No duplicate rule identifiers are allowed (if the rule starts with an
  identifier like ``[R1]``).

The validator writes a short markdown report to
``docs/reproducibility/tie_breaking_validation_report.md``.  If the
validation succeeds the report contains a success message; otherwise it
lists the offending lines.

The script is deliberately lightweight and avoids the ``log_operation``
decorator (which caused a ``TypeError`` in the previous implementation).
It uses the project's ``reproducibility.logs.get_logger`` utility for
optional debugging output.

The script exits with status code ``0`` on success and ``1`` on failure,
satisfying SC‑007's requirement that a successful consistency check returns
a zero exit code.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

# The project provides a simple logger; it accepts no arguments.
try:
    from reproducibility.logs import get_logger
except Exception:  # pragma: no cover
    # Fallback to a no‑op logger if the import fails for any reason.
    class _NoOpLogger:
        def info(self, *args, **kwargs): ...
        def warning(self, *args, **kwargs): ...
        def error(self, *args, **kwargs): ...

    def get_logger() -> _NoOpLogger:  # type: ignore
        return _NoOpLogger()

logger = get_logger()

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_rules(rules_path: Path) -> List[str]:
    """Read the rule file and return a list of its lines."""
    if not rules_path.is_file():
        raise FileNotFoundError(f"Tie‑breaking rules file not found: {rules_path}")
    logger.info("Loading tie‑breaking rules from %s", rules_path)
    return rules_path.read_text(encoding="utf-8").splitlines()


def _validate_rules(lines: List[str]) -> List[str]:
    """
    Validate the list of rule lines.

    Returns a list of error messages; an empty list means the file passed
    all checks.
    """
    errors: List[str] = []
    seen_identifiers: set[str] = set()

    for idx, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            # Blank lines are allowed.
            continue

        # Expect a bullet at the start.
        if not (line.startswith("-") or line.startswith("*")):
            errors.append(f"Line {idx}: does not start with a bullet ('-' or '*').")
            continue

        # Remove the bullet and any surrounding whitespace.
        content = line[1:].strip()
        if not content:
            errors.append(f"Line {idx}: bullet is empty.")
            continue

        # Optional identifier detection, e.g. "[R1] some text"
        if content.startswith("["):
            end_bracket = content.find("]")
            if end_bracket != -1:
                identifier = content[1:end_bracket].strip()
                if identifier:
                    if identifier in seen_identifiers:
                        errors.append(
                            f"Line {idx}: duplicate rule identifier '[{identifier}]'."
                        )
                    else:
                        seen_identifiers.add(identifier)
        # No further structural checks – the rule text itself is free‑form.
    return errors


def _write_report(report_path: Path, errors: List[str]) -> None:
    """Write a markdown validation report."""
    logger.info("Writing validation report to %s", report_path)
    if not errors:
        content = (
            "# Tie‑breaking Rules Validation\n\n"
            "✅ **All tie‑breaking rules are consistent.**\n\n"
            "*Each rule is a non‑empty bullet point and identifiers are unique.*\n"
        )
    else:
        error_list = "\n".join(f"- {e}" for e in errors)
        content = (
            "# Tie‑breaking Rules Validation\n\n"
            "❌ **Inconsistencies detected in tie‑breaking rules.**\n\n"
            "The following problems were found:\n"
            f"{error_list}\n"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(content, encoding="utf-8")


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main() -> int:
    """
    Execute the validator.

    Returns:
        int: Exit status (0 = success, 1 = validation errors).
    """
    # Paths are relative to the repository root.
    project_root = Path(__file__).resolve().parents[2]  # code/reproducibility/..
    rules_file = project_root / "docs" / "reproducibility" / "tie_breaking_rules.md"
    report_file = (
        project_root
        / "docs"
        / "reproducibility"
        / "tie_breaking_validation_report.md"
    )

    try:
        lines = _load_rules(rules_file)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        sys.stderr.write(str(exc) + "\n")
        return 1

    errors = _validate_rules(lines)
    _write_report(report_file, errors)

    # Exit code per SC‑007: 0 on success, 1 on any inconsistency.
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())