"""
Basic sanity test that the PII scanner runs without error on an empty directory.
"""
from __future__ import annotations

import pathlib

from pii_scanner import run_pii_scan

def test_run_pii_scan_on_empty(tmp_path: pathlib.Path):
    # Ensure the directory is empty
    run_pii_scan(base_dir=tmp_path)
    # No exception means pass – the function writes its findings to CSV,
    # which we do not assert here because the directory is empty.
