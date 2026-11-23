"""Convenience wrapper to run the data‑extraction stage.

The quick‑start and test suite expect the full dataset to be present at
``data/raw/commit_pairs.csv`` with at least 500 rows.  This tiny driver
simply invokes the ``code.data_extraction`` module with the appropriate
command‑line flag so that the module inspects ``sys.argv`` and fetches the
required number of commit‑diff pairs.

It is deliberately placed under ``code/`` so that the path utilities
(``paths``) resolve correctly.
"""
from __future__ import annotations

import sys
from code import data_extraction

if __name__ == "__main__":
    # Forward the ``--full`` flag to request the full 500‑row dataset.
    sys.argv = [sys.argv[0], "--full"]
    sys.exit(data_extraction.main())