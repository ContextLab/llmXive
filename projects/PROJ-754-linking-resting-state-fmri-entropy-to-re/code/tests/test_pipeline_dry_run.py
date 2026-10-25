"""
Test suite to ensure the pipeline orchestrator exits cleanly on dry-run.
"""
import pytest
from code.src.pipeline import run_pipeline

def test_run_pipeline_dry_run():
    """
    Verify that run_pipeline with dry_run=True completes without 
    raising exceptions or attempting heavy processing.
    """
    try:
        # This should return immediately due to the dry_run check
        run_pipeline(subjects=5, dry_run=True)
    except Exception as e:
        pytest.fail(f"Pipeline dry-run failed with exception: {e}")