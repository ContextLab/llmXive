import os
import sys
import time
import pytest
from pathlib import Path
import json

# Add project root to path if not already present
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.timing import run_pipeline_script, MAX_RUNTIME_SECONDS, PIPELINE_STAGES

class TestPipelineTiming:
    """
    Integration tests for pipeline timing validation.
    Note: These tests do not run the full 6-hour pipeline in CI,
    but verify the logic and partial execution capabilities.
    """

    def test_run_pipeline_script_returns_tuple(self):
        """Test that run_pipeline_script returns the correct tuple structure."""
        # Use a simple script that we know exists or create a mock
        # For this test, we'll check the return type structure
        # We can't easily test a real pipeline stage without data, 
        # so we test the error handling path with a non-existent file
        success, duration, output = run_pipeline_script("non_existent_script.py")
        
        assert isinstance(success, bool)
        assert isinstance(duration, float)
        assert isinstance(output, str)
        assert success is False
        assert duration >= 0

    def test_max_runtime_constant(self):
        """Verify the max runtime constant is set to 6 hours in seconds."""
        assert MAX_RUNTIME_SECONDS == 6 * 3600

    def test_pipeline_stages_defined(self):
        """Verify that the pipeline stages list is populated."""
        assert len(PIPELINE_STAGES) > 0
        assert isinstance(PIPELINE_STAGES, list)
        
        # Check that paths are strings
        for stage in PIPELINE_STAGES:
            assert isinstance(stage, str)

    def test_script_execution_error_handling(self):
        """Test that execution of a script that doesn't exist is handled gracefully."""
        success, duration, output = run_pipeline_script("code/data/non_existent.py")
        
        assert success is False
        assert "not found" in output.lower() or "No such file" in output

    @pytest.mark.slow
    def test_partial_pipeline_execution(self):
        """
        Execute the first stage (download) to verify the timing infrastructure works.
        This is a 'slow' test because it actually hits the API.
        """
        # We only test the first stage to avoid long runtimes in CI
        # In a real run, all stages would be executed
        if "code/data/download.py" in PIPELINE_STAGES:
            success, duration, output = run_pipeline_script("code/data/download.py")
            
            # We expect this to either succeed or fail due to API limits/data issues,
            # but the timing infrastructure should work
            assert isinstance(success, bool)
            assert duration >= 0
            # The output should contain some log messages or errors
            assert len(output) > 0