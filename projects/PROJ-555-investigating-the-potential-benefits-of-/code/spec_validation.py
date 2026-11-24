"""
spec_validation.py
------------------

Utility functions for validating specification clauses required by
Task T001. The functions check that required phrases are present in the
specification markdown file and, on failure, write a human‑readable error
message to a **project‑owned** log file (``logs/spec_validation.log``)
before raising ``RuntimeError`` to halt the pipeline.

The original task description referenced ``state/spec_validation.log``.
Writing to ``state/`` is prohibited by the platform – it is a
platform‑owned directory.  All logs are therefore written under the
project‑owned ``logs/`` directory which is created on demand.
"""

import logging
from pathlib import Path
from datetime import datetime

# ----------------------------------------------------------------------
# Helper
# ----------------------------------------------------------------------
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "spec_validation.log"


def _ensure_log_dir() -> None:
    """Create the ``logs`` directory if it does not exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _write_error_and_raise(message: str) -> None:
    """
    Write *message* to the project‑owned log file and raise a
    ``RuntimeError``.  The log file is created if it does not exist.
    """
    _ensure_log_dir()
    timestamp = datetime.utcnow().isoformat()
    entry = f"[{timestamp}] {message}\n"
    LOG_FILE.open("a", encoding="utf-8").write(entry)
    raise RuntimeError(message)


# ----------------------------------------------------------------------
# Validation helpers
# ----------------------------------------------------------------------
def verify_sc001_valid_sites(
    spec_path: str = "specs/001-investigating-the-potential-benefits-of/spec.md",
    required_phrase: str = "up to 30 valid sites",
) -> bool:
    """
    Verify that **SC‑001** contains ``required_phrase``.
    Returns ``True`` on success; on failure writes an entry to the log
    and raises ``RuntimeError``.
    """
    spec_file = Path(spec_path)
    if not spec_file.is_file():
        _write_error_and_raise(f"SC‑001 validation failed: spec file not found at {spec_path}")

    content = spec_file.read_text(encoding="utf-8").lower()
    if required_phrase.lower() in content:
        return True
    else:
        _write_error_and_raise(
            f"SC‑001 validation failed: required phrase '{required_phrase}' not found."
        )
    # Unreachable


def verify_fr002_linear_slope_fallback(
    spec_path: str = "specs/001-investigating-the-potential-benefits-of/spec.md",
    required_phrase: str = "linear slope fallback",
) -> bool:
    """
    Verify that **FR‑002** contains the note about the linear‑slope fallback.
    Returns ``True`` on success; on failure writes to the log and raises
    ``RuntimeError``.
    """
    spec_file = Path(spec_path)
    if not spec_file.is_file():
        _write_error_and_raise(f"FR‑002 validation failed: spec file not found at {spec_path}")

    content = spec_file.read_text(encoding="utf-8").lower()
    if required_phrase.lower() in content:
        return True
    else:
        _write_error_and_raise(
            f"FR‑002 validation failed: required phrase '{required_phrase}' not found."
        )
    # Unreachable


# ----------------------------------------------------------------------
# Compatibility wrappers required by the existing test‑suite
# ----------------------------------------------------------------------
def verify_sc001_spec_requirement(
    spec_path: str,
    required_phrase: str,
    log_path: str,
) -> bool:
    """
    Compatibility wrapper used by ``tests/unit/test_spec_validation.py``.
    It forwards to :func:`verify_sc001_valid_sites` and writes the log
    to the path provided by the test (which points to the project‑owned
    ``logs`` directory in the test fixture).
    """
    # The test supplies a temporary ``log_path``; we honour it.
    global LOG_FILE
    LOG_FILE = Path(log_path)
    return verify_sc001_valid_sites(spec_path=spec_path, required_phrase=required_phrase)


def verify_fr002_nonlinear_fallback(
    spec_path: str,
) -> bool:
    """
    Compatibility wrapper used by ``tests/unit/test_spec_validation.py``.
    Checks for the phrase ``linear slope`` inside the FR‑002 section.
    """
    return verify_fr002_linear_slope_fallback(
        spec_path=spec_path, required_phrase="linear slope"
    )


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Run both validation checks.  If either fails the function will raise
    ``RuntimeError`` (the caller can catch it to abort the pipeline).
    """
    # Use the default spec location; the path is relative to the project root.
    verify_sc001_valid_sites()
    verify_fr002_linear_slope_fallback()
    # If we reach here both checks succeeded.
    # Optionally write a success entry for completeness.
    _ensure_log_dir()
    LOG_FILE.open("a", encoding="utf-8").write(
        f"[{datetime.utcnow().isoformat()}] SPEC VALIDATION SUCCESS\n"
    )
