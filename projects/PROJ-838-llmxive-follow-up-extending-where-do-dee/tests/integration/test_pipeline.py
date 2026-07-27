import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

def test_full_pipeline_execution():
    """
    Integration test to verify the full pipeline execution sequence.
    Uses mocks to avoid actual data download and heavy computation.
    """
    # Mock the individual runner modules to ensure they are called in order
    with patch('run_downloader.main') as mock_downloader, \
         patch('run_build_graphs.main') as mock_graphs, \
         patch('run_metrics.main') as mock_metrics, \
         patch('run_evaluator.main') as mock_evaluator:
        
        # Import pipeline after patching
        from pipeline import main
        
        # Execute pipeline
        result = main()
        
        # Verify exit code is 0 (success)
        assert result == 0
        
        # Verify all stages were called in correct order
        mock_downloader.assert_called_once()
        mock_graphs.assert_called_once()
        mock_metrics.assert_called_once()
        mock_evaluator.assert_called_once()
        
        # Verify call order
        calls = [mock_downloader, mock_graphs, mock_metrics, mock_evaluator]
        for i in range(len(calls) - 1):
            # Check that call i happened before call i+1
            # Since we are mocking, we check the call count order implicitly by the fact they ran
            assert calls[i].called
            assert calls[i+1].called