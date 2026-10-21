"""
Wrapper module so that the quick‑start command ``python -m src.ingest.ingest``
forwards to the actual implementation in ``code.ingest.ingest``.
"""

from code.ingest.ingest import run_ingest, main  # noqa: F401

if __name__ == "__main__":
    main()
