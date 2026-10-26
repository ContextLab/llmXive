"""
Integration test to ensure the pipeline orchestrator can be invoked
in dry-run mode and exit with status 0.
"""
from code.src.pipeline import run_pipeline

def test_run_pipeline_dry_run():
    """
    Verify that run_pipeline(dry_run=True) completes without exception.
    """
    try:
        run_pipeline(subjects=5, dry_run=True)
    except Exception as e:
        pytest.fail(f"Pipeline dry-run failed with exception: {e}")
