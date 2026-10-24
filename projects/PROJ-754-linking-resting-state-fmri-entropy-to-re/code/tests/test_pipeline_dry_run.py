"""
Test that the pipeline orchestrator exits cleanly during a dry-run.
"""
import pytest
from code.src.pipeline import run_pipeline

def test_run_pipeline_dry_run():
    """
    Verify that run_pipeline returns without error when dry_run=True.
    This ensures the orchestrator logic is syntactically correct and 
    handles the dry-run guard properly.
    """
    try:
        # Dry run should return immediately without attempting downloads or processing
        run_pipeline(subjects=5, dry_run=True)
    except Exception as e:
        pytest.fail(f"Pipeline dry-run failed with exception: {e}")
