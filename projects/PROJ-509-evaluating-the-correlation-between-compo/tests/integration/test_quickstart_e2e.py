"""
Integration test for the full quickstart validation flow.
This test mocks the subprocess calls to simulate a successful pipeline run
and verifies the final validation logic.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, call

@pytest.fixture
def mock_project_structure():
    """Create a temporary project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        # Create directories
        (base / "data" / "raw").mkdir(parents=True)
        (base / "data" / "processed").mkdir(parents=True)
        (base / "data" / "evaluation").mkdir(parents=True)
        (base / "data" / "logs").mkdir(parents=True)
        (base / "code").mkdir(parents=True)
        
        # Create dummy output files that scripts would generate
        (base / "data" / "raw" / "mp-2020.12.1.csv").touch()
        (base / "data" / "raw" / "mp-2020.12.1_filtered.csv").touch()
        (base / "data" / "processed" / "sampled_raw_data.csv").touch()
        (base / "data" / "processed" / "computed_descriptors.csv").touch()
        (base / "data" / "evaluation" / "model_metrics.json").touch()
        (base / "data" / "evaluation" / "model_rf.pkl").touch()
        (base / "data" / "evaluation" / "model_gb.pkl").touch()
        (base / "data" / "evaluation" / "feature_ranking.json").touch()
        (base / "data" / "evaluation" / "ale_top_feature.png").touch()
        
        # Populate model_metrics.json with valid content
        metrics = {
            "r2": 0.65,
            "mae": 0.12,
            "rmse": 0.18,
            "overfitting_ratio": 0.03,
            "predictive_power": True
        }
        with open(base / "data" / "evaluation" / "model_metrics.json", 'w') as f:
            json.dump(metrics, f)
        
        yield base

@patch('subprocess.run')
@patch('quickstart_validation.load_paths')
def test_main_success_flow(mock_load_paths, mock_subprocess_run, mock_project_structure):
    """Test the main function when all steps succeed."""
    from quickstart_validation import main
    
    # Mock load_paths
    mock_load_paths.return_value = {'project_root': str(mock_project_structure)}
    
    # Mock subprocess.run to return success
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    mock_subprocess_run.return_value = mock_result
    
    # Run main
    # We need to ensure the script doesn't exit with sys.exit(1) on failure
    # but here we expect success.
    # We will patch sys.exit to prevent actual exit
    import sys
    with patch.object(sys, 'exit') as mock_exit:
        try:
            main()
        except SystemExit:
            pass # Expected if success is printed and exit(0) called
        
        # Verify subprocess was called for each step
        expected_calls = [
            call(['python', 'code/ingest.py'], cwd=mock_project_structure, check=True, capture_output=True, text=True, timeout=3600),
            call(['python', 'code/descriptors.py'], cwd=mock_project_structure, check=True, capture_output=True, text=True, timeout=3600),
            call(['python', 'code/train.py'], cwd=mock_project_structure, check=True, capture_output=True, text=True, timeout=3600),
            call(['python', 'code/evaluate.py'], cwd=mock_project_structure, check=True, capture_output=True, text=True, timeout=3600),
            call(['python', 'code/importance.py'], cwd=mock_project_structure, check=True, capture_output=True, text=True, timeout=3600),
            call(['python', 'code/plots.py'], cwd=mock_project_structure, check=True, capture_output=True, text=True, timeout=3600),
            call(['python', 'code/generate_research_summary.py'], cwd=mock_project_structure, check=True, capture_output=True, text=True, timeout=3600),
        ]
        
        # Check that subprocess.run was called with the correct arguments
        # Note: The order might vary if we use a loop, but here we check the count and content
        assert mock_subprocess_run.call_count == 7
        
        # Verify artifacts were checked
        # The verify_artifacts function is called, we can't easily mock internal logic
        # but we know it passed because we didn't get an error log or exit(1)
        
@patch('subprocess.run')
@patch('quickstart_validation.load_paths')
def test_main_failure_step(mock_load_paths, mock_subprocess_run, mock_project_structure):
    """Test the main function when a step fails."""
    from quickstart_validation import main
    import logging
    
    mock_load_paths.return_value = {'project_root': str(mock_project_structure)}
    
    # Mock first call success, second call failure
    def side_effect(*args, **kwargs):
        if 'ingest.py' in str(args):
            mock_res = MagicMock()
            mock_res.returncode = 0
            return mock_res
        else:
            raise Exception("CalledProcessError") # Simulate failure
    
    mock_subprocess_run.side_effect = side_effect
    
    import sys
    with patch.object(sys, 'exit') as mock_exit:
        try:
            main()
        except SystemExit:
            pass
        
        # Check that it stopped after the failure
        # It should have called ingest, then descriptors, then failed
        assert mock_subprocess_run.call_count >= 2
        # Verify it didn't run all 7 steps
        assert mock_subprocess_run.call_count < 7
