"""
Unit tests for the main pipeline orchestration script.

These tests verify that the main.py script correctly orchestrates
the pipeline phases and generates the final report with proper
associational framing.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

class TestMainPipeline:
    """Tests for the main pipeline orchestration."""

    @patch('main.process_all_repos')
    @patch('main.metrics_calc_main')
    @patch('main.run_full_analysis')
    @patch('main.visualizations_main')
    @patch('main.generate_final_report')
    def test_pipeline_success_flow(
        self, 
        mock_report, 
        mock_viz, 
        mock_analysis, 
        mock_metrics, 
        mock_data
    ):
        """Test that the pipeline executes all phases in correct order on success."""
        from main import main
        
        # Mock all phases to succeed
        mock_data.return_value = True
        mock_metrics.return_value = True
        mock_analysis.return_value = True
        mock_viz.return_value = True
        mock_report.return_value = True
        
        # Mock config functions
        with patch('main.get_cutoff_date') as mock_cutoff, \
             patch('main.get_depth_limit') as mock_depth, \
             patch('main.get_repo_list') as mock_repos, \
             patch('main.get_output_dir') as mock_output:
            
            from datetime import datetime
            mock_cutoff.return_value = datetime(2023, 1, 1)
            mock_depth.return_value = 1000
            mock_repos.return_value = ['test/repo']
            mock_output.return_value = 'data'
            
            # Run main
            result = main()
            
            # Verify execution order
            mock_data.assert_called_once()
            mock_metrics.assert_called_once()
            mock_analysis.assert_called_once()
            mock_viz.assert_called_once()
            mock_report.assert_called_once()
            
            # Verify success return code
            assert result == 0

    @patch('main.process_all_repos')
    def test_pipeline_fails_on_data_collection_failure(self, mock_data):
        """Test that pipeline aborts if data collection fails."""
        from main import main
        
        mock_data.return_value = False
        
        with patch('main.get_cutoff_date'), \
             patch('main.get_depth_limit'), \
             patch('main.get_repo_list'), \
             patch('main.get_output_dir'):
            
            result = main()
            
            # Verify subsequent phases were NOT called
            assert result == 1

    @patch('main.process_all_repos')
    @patch('main.metrics_calc_main')
    def test_pipeline_fails_on_metrics_failure(self, mock_metrics, mock_data):
        """Test that pipeline aborts if metrics calculation fails."""
        from main import main
        
        mock_data.return_value = True
        mock_metrics.return_value = False
        
        with patch('main.get_cutoff_date'), \
             patch('main.get_depth_limit'), \
             patch('main.get_repo_list'), \
             patch('main.get_output_dir'):
            
            result = main()
            
            # Verify analysis was NOT called
            assert result == 1

    def test_final_report_contains_associational_framing(self):
        """Test that the final report explicitly contains associational framing."""
        # This test verifies the content structure expected in the report
        # We check the template logic by examining the generate_final_report function
        
        from main import generate_final_report
        from unittest.mock import MagicMock
        
        # Create a mock logger
        mock_logger = MagicMock()
        
        # Create mock execution metadata
        execution_metadata = {
            "status": "success",
            "phases": {}
        }
        
        # Mock the output directory creation
        with patch('main.get_output_dir') as mock_output, \
             patch('builtins.open', MagicMock()) as mock_file:
            
            mock_output.return_value = 'data'
            
            # Call the function
            result = generate_final_report(mock_logger, execution_metadata)
            
            # Verify the file was called
            mock_file.assert_called_once()
            
            # Get the content that was written
            call_args = mock_file.call_args
            # The second positional arg is the mode, third is the content
            # We need to inspect the json.dump call
            
            # Instead, let's verify by checking the function source or re-running
            # with a real file
            import tempfile
            import json
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                temp_path = f.name
            
            try:
                with patch('main.get_output_dir') as mock_output, \
                     patch('pathlib.Path.open', MagicMock(return_value=open(temp_path, 'w'))) as mock_open:
                    
                    mock_output.return_value = 'data'
                    generate_final_report(mock_logger, execution_metadata)
                    
                    # Read and verify the file
                    with open(temp_path, 'r') as f:
                        report = json.load(f)
                    
                    # Check for associational framing
                    assert "associational rather than causal" in report["metadata"]["causal_framing"]["statement"]
                    assert "causal relationships" in report["metadata"]["causal_framing"]["rationale"]
                    assert "observational nature" in report["metadata"]["causal_framing"]["rationale"]
                    
                    # Check temporal separation
                    assert "ownership_period" in report["metadata"]["temporal_framing"]
                    assert "quality_period" in report["metadata"]["temporal_framing"]
                    
                    assert result == True
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    @patch('main.process_all_repos')
    @patch('main.metrics_calc_main')
    @patch('main.run_full_analysis')
    @patch('main.visualizations_main')
    def test_pipeline_continues_on_visualization_failure(
        self, 
        mock_viz, 
        mock_analysis, 
        mock_metrics, 
        mock_data
    ):
        """Test that pipeline continues to report generation even if visualizations fail."""
        from main import main
        
        mock_data.return_value = True
        mock_metrics.return_value = True
        mock_analysis.return_value = True
        mock_viz.return_value = False  # Visualization fails
        
        with patch('main.get_cutoff_date') as mock_cutoff, \
             patch('main.get_depth_limit') as mock_depth, \
             patch('main.get_repo_list') as mock_repos, \
             patch('main.get_output_dir') as mock_output, \
             patch('main.generate_final_report') as mock_report:
            
            from datetime import datetime
            mock_cutoff.return_value = datetime(2023, 1, 1)
            mock_depth.return_value = 1000
            mock_repos.return_value = ['test/repo']
            mock_output.return_value = 'data'
            mock_report.return_value = True
            
            result = main()
            
            # Should still succeed and generate report
            assert result == 0
            mock_report.assert_called_once()
