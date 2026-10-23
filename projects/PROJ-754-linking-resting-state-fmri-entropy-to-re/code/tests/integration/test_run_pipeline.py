"""
Integration test that the pipeline can be invoked in dry‑run mode.
"""
import sys

from src import run_pipeline


def test_pipeline_dry_run(monkeypatch):
    """
    Run the pipeline with ``--dry-run``; it should exit without raising.
    """
    # Patch sys.argv for the entry‑point.
    monkeypatch.setattr(sys, "argv", ["run_pipeline", "--subjects", "5", "--dry-run"])
    # The function should complete without exception.
    run_pipeline.main()
