"""
Integration test for the pipeline orchestrator.

The test imports the public ``run_pipeline`` function from the top‑level
``src`` package (which re‑exports the implementation under ``code.src``)
and executes a dry‑run.  The dry‑run should complete without raising any
exception.
"""
import pytest

from src import run_pipeline


def test_dry_run_completes():
    # The orchestrator should return ``None`` and not raise.
    run_pipeline(subjects=5, dry_run=True)
