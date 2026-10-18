"""
spec_validation.py
------------------

This module verifies that the core specification clauses required for the
project are present. Specifically it checks:

* SC‑001 contains the phrase “up to 30 valid sites”.
* FR‑002 contains the phrase “linear slope fallback”.

If any check fails, a descriptive error entry is written to
`state/spec_validation.log` and a ``RuntimeError`` is raised to halt the
pipeline.
"""

import logging
from pathlib import Path
from datetime import datetime

from logging_config import setup_logging, get_logger

# Initialise a logger for this module
setup_logging()
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _write_error_and_raise(message: str) -> None:
    """
    Write *message* to ``state/spec_validation.log`` and raise a
    ``RuntimeError``.  The log file is created if it does not exist.
    """
    log_path = Path("state") / "spec_validation.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().isoformat() + "Z"
    entry = f"[{timestamp}] {message}\n"

    # Append the error entry
    with log_path.open("a", encoding="utf-8") as f:
        f.write(entry)

    # Also log to the standard logger for visibility
    log.error(message)

    raise RuntimeError(message)


# ----------------------------------------------------------------------
# Verification functions
# ----------------------------------------------------------------------
def verify_sc001_valid_sites(
    spec_path: str = "specs/001-investigating-the-potential-benefits-of/spec.md",
    required_phrase: str = "up to 30 valid sites",
) -> bool:
    """
    Verify that SC‑001 in the specification contains *required_phrase*.

    Returns ``True`` if the phrase is found, otherwise ``False``.
    """
    spec_file = Path(spec_path)
    if not spec_file.is_file():
        _write_error_and_raise(f"Specification file not found: {spec_path}")

    content = spec_file.read_text(encoding="utf-8")
    if required_phrase in content:
        log.info("SC‑001 validation succeeded.")
        return True
    else:
        _write_error_and_raise(
            f"SC‑001 validation failed – missing phrase: '{required_phrase}'."
        )
        return False  # Unreachable – kept for type checkers


def verify_fr002_linear_slope_fallback(
    spec_path: str = "specs/001-investigating-the-potential-benefits-of/spec.md",
    required_phrase: str = "linear slope fallback",
) -> bool:
    """
    Verify that FR‑002 in the specification contains *required_phrase*.

    Returns ``True`` if the phrase is found, otherwise ``False``.
    """
    spec_file = Path(spec_path)
    if not spec_file.is_file():
        _write_error_and_raise(f"Specification file not found: {spec_path}")

    content = spec_file.read_text(encoding="utf-8")
    if required_phrase in content:
        log.info("FR‑002 validation succeeded.")
        return True
    else:
        _write_error_and_raise(
            f"FR‑002 validation failed – missing phrase: '{required_phrase}'."
        )
        return False  # Unreachable – kept for type checkers


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Run all specification checks required for T001.

    If any check fails, an error is logged to ``state/spec_validation.log``
    and a ``RuntimeError`` is raised.
    """
    # Perform SC‑001 validation
    verify_sc001_valid_sites()

    # Perform FR‑002 validation
    verify_fr002_linear_slope_fallback()

    log.info("All specification validations passed successfully.")


if __name__ == "__main__":
    # Allow the script to be executed directly (`python code/spec_validation.py`)
    main()
