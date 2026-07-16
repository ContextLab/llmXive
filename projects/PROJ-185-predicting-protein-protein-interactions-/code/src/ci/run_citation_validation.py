#!/usr/bin/env python3
"""
CI entry point for citation validation.

This script invokes the Reference‑Validator Agent implemented in
``src.ci.validate_citations``.  It exits with a non‑zero status code if any
citation mismatch is detected, causing the CI pipeline to fail.

The ``validate_citations.main`` function is expected to perform the actual
validation work and return ``True`` when all citations are correct or
``False`` when mismatches are found.  If the function raises an exception,
the script also exits with a non‑zero code.
"""

import sys
from src.ci.validate_citations import main as validate_citations_main

def _run_validation() -> int:
    """
    Run the citation validator and return an appropriate exit code.

    Returns
    -------
    int
        ``0`` if validation succeeded (no mismatches),
        ``1`` otherwise.
    """
    try:
        result = validate_citations_main()
        # If the validator returns a truthy value we consider it a success.
        # Any falsy value (e.g., ``False`` or ``None``) indicates failure.
        return 0 if result else 1
    except Exception:
        # Unexpected errors should also cause CI to fail.
        return 1

def main() -> None:
    """Entry point for the script."""
    exit_code = _run_validation()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
