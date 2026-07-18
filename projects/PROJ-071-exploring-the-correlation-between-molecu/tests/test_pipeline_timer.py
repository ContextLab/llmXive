"""
Tests for the pipeline timer and orchestration logic.
Verifies that the timer script correctly measures time and writes metrics.
"""
import os
import sys
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.run_pipeline_timer import main as run_pipeline_main

@pytest.fixture
def mock_stage_funcs():
    """Mock the stage functions to simulate execution without real data processing."""
    with patch('code.run_pipeline_timer.ingest_main') as mock_ingest, \
         patch('code.run_pipeline_timer.descriptors_main') as mock_desc, \
         patch('code.run_pipeline_timer.standardize_main') as mock_std, \
         patch('code.run_pipeline_timer.analysis_main') as mock_analysis, \
         patch('code.run_pipeline_timer.viz_main') as mock_viz, \
         patch('code.run_pipeline_timer.report_main') as mock_report:
        
        # Simulate small delays to ensure timing is non-zero
        def slow_mock(*args, **kwargs):
            time.sleep(0.01)
        
        mock_ingest.side_effect = slow_mock
        mock_desc.side_effect = slow_mock
        mock_std.side_effect = slow_mock
        mock_analysis.side_effect = slow_mock
        mock_viz.side_effect = slow_mock
        mock_report.side_effect = slow_mock

        yield {
            'ingest': mock_ingest,
            'descriptors': mock_desc,
            'standardize': mock_std,
            'analysis': mock_analysis,
            'viz': mock_viz,
            'report': mock_report
        }

def test_pipeline_timer_writes_metrics(mock_stage_funcs, tmp_path):
    """
    Verify that the pipeline timer writes a valid metrics JSON file
    with expected keys and non-zero durations.
    """
    # Temporarily override the output path to use tmp_path
    # We patch the project_root resolution inside the function
    original_run = run_pipeline_main.__code__
    
    # We need to patch the Path resolution or the file write location
    # Since the script uses `project_root / "data" / "output"`, we can
    # patch the `Path` class or the specific path logic.
    # Easier: patch the `open` call or the `Path` creation.
    
    metrics_written = {}

    def mock_json_dump(data, f, indent=None):
        metrics_written.update(data)

    with patch('code.run_pipeline_timer.Path') as MockPath:
        # Mock the project_root path
        mock_project_root = MagicMock()
        mock_project_root.__truediv__ = lambda self, other: tmp_path / other
        MockPath.return_value = mock_project_root
        MockPath.return_value.__truediv__ = lambda self, other: tmp_path / other
        
        # Ensure parent exists
        (tmp_path / "data" / "output").mkdir(parents=True, exist_ok=True)

        with patch('json.dump', side_effect=mock_json_dump):
            # Run the main logic
            try:
                run_pipeline_main()
            except SystemExit:
                pass # Expected if no args or logging setup issues in test env
            except Exception:
                # If it fails due to logging config or other test env issues,
                # we still check if metrics were attempted to be written
                pass

    # Assertions on the metrics structure
    assert 'total_duration_seconds' in metrics_written
    assert 'stages' in metrics_written
    assert metrics_written['status'] == 'completed'
    
    # Check that all stages are recorded
    expected_stages = ['ingest', 'descriptors', 'standardization', 'analysis', 'visualization', 'reporting']
    for stage in expected_stages:
        assert stage in metrics_written['stages'], f"Missing stage: {stage}"
        # Verify duration is positive (simulated delay)
        assert metrics_written['stages'][stage] > 0, f"Stage {stage} has zero duration"

def test_pipeline_timer_handles_failure(mock_stage_funcs, tmp_path):
    """
    Verify that if a stage fails, the metrics file records 'failed' status
    and the error message.
    """
    mock_stage_funcs['analysis'].side_effect = RuntimeError("Simulated analysis failure")

    metrics_written = {}

    def mock_json_dump(data, f, indent=None):
        metrics_written.update(data)

    with patch('code.run_pipeline_timer.Path') as MockPath:
        mock_project_root = MagicMock()
        mock_project_root.__truediv__ = lambda self, other: tmp_path / other
        MockPath.return_value = mock_project_root
        MockPath.return_value.__truediv__ = lambda self, other: tmp_path / other
        (tmp_path / "data" / "output").mkdir(parents=True, exist_ok=True)

        with patch('json.dump', side_effect=mock_json_dump):
            with pytest.raises(RuntimeError):
                run_pipeline_main()

    assert metrics_written['status'] == 'failed'
    assert 'error' in metrics_written
    assert 'Simulated analysis failure' in metrics_written['error']