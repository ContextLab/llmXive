"""
Performance Tests for the Stellar Flare Analysis Pipeline.

Tests verify that the pipeline meets the SC-004 requirement of completing
within 60 seconds.
"""
import pytest
import time
import sys
from pathlib import Path

# Add project root to path if running from tests directory
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from performance_benchmark import run_benchmark, MAX_DURATION_SECONDS

class TestPipelinePerformance:
    """Test suite for pipeline performance constraints."""

    def test_total_pipeline_duration(self):
        """
        Verify that the full pipeline completes within the 60-second limit.
        
        This test runs the actual pipeline and asserts the total duration.
        Note: This test may take up to 60 seconds to run.
        """
        # Set a slightly higher timeout for pytest if running in CI
        # but the assertion logic remains strict against the 60s limit.
        success, timings = run_benchmark()
        
        assert success, f"Pipeline execution failed or exceeded time limit. Total time: {timings.get('total', 0):.2f}s"
        assert 'total' in timings, "Timings dictionary missing 'total' key"
        assert timings['total'] <= MAX_DURATION_SECONDS, (
            f"Pipeline exceeded maximum allowed duration of {MAX_DURATION_SECONDS}s. "
            f"Actual time: {timings['total']:.2f}s"
        )

    def test_individual_stage_performance(self):
        """
        Verify that no single stage takes an unreasonable amount of time.
        
        While the total must be < 60s, we also check that no single stage
        dominates the runtime disproportionately (e.g., > 50s for one stage).
        This helps identify bottlenecks.
        """
        success, timings = run_benchmark()
        
        if not success:
            pytest.skip("Full pipeline failed, cannot analyze individual stages")

        # Define a soft limit for individual stages (e.g., 55s)
        # If one stage takes > 55s, it leaves no room for others.
        soft_limit = 55.0 
        
        for stage, duration in timings.items():
            if stage == 'total':
                continue
            # Only assert if the stage actually ran (duration > 0)
            if duration > 0:
                # We use a warning-style assertion here to allow the test to pass
                # even if a stage is slow, but log the issue.
                # In a strict CI environment, this might be a hard fail.
                assert duration < soft_limit, (
                    f"Stage '{stage}' took {duration:.2f}s, which is approaching the total limit. "
                    f"Consider optimizing."
                )