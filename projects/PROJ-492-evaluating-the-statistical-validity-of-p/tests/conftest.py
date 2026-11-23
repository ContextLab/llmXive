"""
Pytest configuration that ensures the corpus curation script runs before any
test collection.  This guarantees that ``tests/test_curate_corpus.py`` sees
the required ``data/input/urls.csv``, ``data/raw/*.html`` snapshots and
``data/checksums.txt`` files produced by ``code/src/audit/curate_corpus.py``.
"""

import pytest

# Import the curation function directly – this avoids spawning a subprocess
# and works even when the repository is executed inside the isolated
# evaluation environment.
from code.src.audit.curate_corpus import main as curate_main


def pytest_sessionstart(session):
    """
    Hook executed once when the pytest session starts.  It runs the
    curation script and aborts the test run if the script fails.
    """
    try:
        curate_main()
    except Exception as exc:
        # Re‑raise so pytest reports the failure as a setup error.
        raise RuntimeError(f"Corpus curation failed during pytest setup: {exc}") from exc