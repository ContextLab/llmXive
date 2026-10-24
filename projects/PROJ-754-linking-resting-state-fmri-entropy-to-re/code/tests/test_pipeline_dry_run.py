import pytest
from code.src.pipeline import run_pipeline

def test_run_pipeline_dry_run():
    """
    Verify that the orchestrator exits cleanly when dry_run=True.
    This satisfies the T001 requirement that run_pipeline exits with status 0 on a dry-run.
    """
    try:
        # subjects=5 is the default requested in T001
        run_pipeline(subjects=5, dry_run=True)
    except Exception as e:
        pytest.fail(f"run_pipeline raised an unexpected exception during dry-run: {e}")
