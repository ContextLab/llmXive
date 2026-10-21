"""
src/ingest.py
---------------
Public wrapper for the ingestion pipeline.

The core implementation lives in ``code/ingest/ingest.py``.  This module
simply re‑exports the public functions so that downstream code can import
``src.ingest`` in a conventional ``src.*`` package layout.
"""
from code.ingest.ingest import run_ingest, main  # noqa: F401,F403
