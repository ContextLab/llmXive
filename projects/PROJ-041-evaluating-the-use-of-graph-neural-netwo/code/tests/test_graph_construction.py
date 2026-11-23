"""
test_graph_construction.py
--------------------------

Minimal sanity test that ensures the raw CTU‑13 CSV created by the
``download_ctu13`` script exists and is non‑empty. This test is part of
the T001 verification suite and is executed via ``pytest``.
"""

import os

from llmxive_toolkit import paths


def test_raw_ctu13_csv_exists():
    """
    Verify that the CSV file produced by ``code/data/download_ctu13.py``
    exists under ``data/raw`` and contains at least one byte of data.
    """
    csv_path = paths.data("raw", "ctu13_scenario1.csv")
    assert csv_path.exists(), f"Expected CSV at {csv_path} to exist"
    assert csv_path.stat().st_size > 0, "CSV file is empty"