"""
Tests for the pipeline execution and timing measurement (T041).
"""
import os
import sys
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.pipeline_runner import run_pipeline, main

class TestPipelineRunner:
    """Tests for pipeline execution timing and structure."""

    @pytest.fixture
    def mock_stages(self):
        """Mock the individual stage functions to avoid full execution."""
        with patch('code.pipeline_runner.ingest_main') as mock_ingest, \
             patch('code.pipeline_runner.descriptors_main') as mock_desc, \
             patch('code.pipeline_runner.standardize_main') as mock_std, \
             patch('code.pipeline_runner.analysis_main') as mock_analysis, \
             patch('code.pipeline_runner.viz_main') as mock_viz, \
             patch('code.pipeline_runner.report_main') as mock_report:
            
            # Simulate different execution times for each stage
            def slow_side_effect(*args, **kwargs):
                time.sleep(0.01)  # Small delay to simulate work
            
            mock_ingest.side_effect = slow_side_effect
            mock_desc.side_effect = slow_side_effect
            mock_std.side_effect = slow_side_effect
            mock_analysis.side_effect = slow_side_effect
            mock_viz.side_effect = slow_side_effect
            mock_report.side_effect = slow_side_effect
            
            yield {
                'ingest': mock_ingest,
                'descriptors': mock_desc,
                'standardize': mock_std,
                'analysis': mock_analysis,
                'viz': mock_viz,
                'report': mock_report
            }

    def test_pipeline_creates_timing_file(self, mock_stages, tmp_path):
        """Verify that the pipeline creates the timing output file."""
        # Create a temporary output directory
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        with patch('code.pipeline_runner.project_root', tmp_path):
            results = run_pipeline()
        
        # Verify timing file was created
        timing_file = tmp_path / "data" / "processed" / "pipeline_timing.json"
        assert timing_file.exists(), "Timing file should be created"
        
        # Verify file contains valid JSON
        with open(timing_file, 'r') as f:
            data = json.load(f)
        
        assert 'total_duration_seconds' in data
        assert 'stages' in data
        assert len(data['stages']) == 6  # All 6 stages

    def test_pipeline_timing_structure(self, mock_stages, tmp_path):
        """Verify the structure and content of timing results."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        with patch('code.pipeline_runner.project_root', tmp_path):
            results = run_pipeline()
        
        # Verify total duration is positive
        assert results['total_duration_seconds'] > 0
        
        # Verify all stages are recorded
        stage_names = [s['stage'] for s in results['stages']]
        expected_stages = ['Ingestion', 'Descriptors', 'Standardization', 
                         'Analysis', 'Visualization', 'Reporting']
        assert stage_names == expected_stages
        
        # Verify each stage has required fields
        for stage in results['stages']:
            assert 'stage' in stage
            assert 'duration_seconds' in stage
            assert 'status' in stage
            assert stage['status'] == 'completed'
            assert stage['duration_seconds'] >= 0

    def test_pipeline_handles_failure(self, mock_stages, tmp_path):
        """Verify pipeline handles stage failures correctly."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Make analysis stage fail
        mock_stages['analysis'].side_effect = RuntimeError("Analysis failed")
        
        with patch('code.pipeline_runner.project_root', tmp_path):
            with pytest.raises(RuntimeError, match="Analysis failed"):
                run_pipeline()
        
        # Verify timing file was still created with failure info
        timing_file = tmp_path / "data" / "processed" / "pipeline_timing.json"
        assert timing_file.exists()
        
        with open(timing_file, 'r') as f:
            data = json.load(f)
        
        assert data['status'] == 'failed'
        assert 'error' in data
        assert 'completed_stages' in data

    def test_main_return_code_success(self, mock_stages, tmp_path, capsys):
        """Verify main() returns 0 on success."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        with patch('code.pipeline_runner.project_root', tmp_path):
            with patch('code.pipeline_runner.setup_logging'):
                with patch('code.pipeline_runner.get_logger'):
                    with patch('code.pipeline_runner.get_config'):
                        with patch('code.pipeline_runner.ensure_directories'):
                            result = main()
        
        assert result == 0
        captured = capsys.readouterr()
        assert "successfully" in captured.out.lower()

    def test_main_return_code_failure(self, mock_stages, tmp_path, capsys):
        """Verify main() returns 1 on failure."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        mock_stages['viz'].side_effect = ValueError("Visualization error")
        
        with patch('code.pipeline_runner.project_root', tmp_path):
            with patch('code.pipeline_runner.setup_logging'):
                with patch('code.pipeline_runner.get_logger'):
                    with patch('code.pipeline_runner.get_config'):
                        with patch('code.pipeline_runner.ensure_directories'):
                            result = main()
        
        assert result == 1
        captured = capsys.readouterr()
        assert "failed" in captured.out.lower()

    def test_timing_accuracy(self, mock_stages, tmp_path):
        """Verify timing measurements are reasonably accurate."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Set known delays
        delay = 0.05
        mock_stages['ingest'].side_effect = lambda: time.sleep(delay)
        mock_stages['descriptors'].side_effect = lambda: time.sleep(delay)
        
        with patch('code.pipeline_runner.project_root', tmp_path):
            results = run_pipeline()
        
        # Total time should be at least the sum of delays (with some tolerance)
        min_expected_time = delay * 6  # 6 stages
        assert results['total_duration_seconds'] >= min_expected_time * 0.8, \
            f"Timing too short: {results['total_duration_seconds']}s vs expected {min_expected_time}s"
        
        # Individual stage times should also reflect the delay
        for stage in results['stages']:
            assert stage['duration_seconds'] >= delay * 0.8, \
                f"Stage {stage['stage']} timing inaccurate: {stage['duration_seconds']}s"
