"""
Wrapper that re‑exports the ingestion functions from ``code/ingest/ingest.py``.
This ensures imports such as ``from src.ingest.ingest import run_ingest`` work
without modifying the existing implementation.
"""

from code.ingest.ingest import *  # noqa: F401,F403

if __name__ == "__main__":
    from code.ingest.ingest import main
    main()