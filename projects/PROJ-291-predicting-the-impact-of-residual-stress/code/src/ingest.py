"""
src/ingest.py
---------------
Public wrapper for the ingestion pipeline.

The core implementation lives in ``code/ingest/ingest.py``.  This module
simply re‑exports the public functions so that downstream code can import
``src.ingest`` in a conventional ``src.*`` package layout.
"""
from code.ingest.ingest import run_ingest, main  # noqa: F401,F403

# When this module is executed directly (e.g. ``python -m src.ingest.ingest``)
# we forward to the real CLI entry point defined in ``code.ingest.ingest``.
# This makes the wrapper behave exactly like the original implementation
# while keeping the import‑only behaviour for library users.
if __name__ == "__main__":
    main()
