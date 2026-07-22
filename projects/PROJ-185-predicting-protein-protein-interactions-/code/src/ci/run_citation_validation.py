"""
Citation verification entry point for CI.

This script is intended to be invoked during continuous integration to ensure
that all markdown (``*.md``) and code (``*.py``) files in the repository contain
valid citations.  It delegates the heavy‑lifting to :pymod:`src.ci.validate_citations`,
which implements the actual crawling, URL extraction and validation logic.

The script exits with status ``0`` when all citations are valid and with a non‑zero
status when any citation fails validation.  CI pipelines can therefore simply run
this module and fail the job if the exit code is non‑zero.
"""

import sys
from src.ci.validate_citations import main as validate_citations_main

def main() -> None:
    """
    Run the citation validator and propagate its exit status.

    The underlying ``validate_citations_main`` function performs:
    * Discovery of target files (``*.md`` and ``*.py``) under the repository root.
    * Extraction of URLs from those files.
    * HTTP ``HEAD`` requests to verify that each URL is reachable and returns a
      successful status code (2xx/3xx).
    * Reporting of any failures to ``stderr`` and returning a non‑zero exit code.

    This wrapper exists so that CI can invoke ``python -m src.ci.run_citation_validation``
    without needing to know the internals of the validator.
    """
    # ``validate_citations_main`` returns an integer exit code.
    # ``sys.exit`` will raise ``SystemExit`` with that code, which is the
    # conventional way for a CLI entry point to signal success/failure.
    exit_code = validate_citations_main()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
