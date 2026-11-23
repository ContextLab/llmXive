import pytest
import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.profiler import profile_pipeline_entrypoint, save_profile_results


class TestProfiler:
    
    def test_save_profile_results_creates_file(self, tmp_path):
        """Test that save_profile_results creates the markdown file."""
        # Mock a profiler object
        mock_profiler = MagicMock()
        mock_profiler.enable = MagicMock()
        mock_profiler.disable = MagicMock()
        
        # Mock the Stats class to return predictable output
        with patch('utils.profiler.pstats.Stats') as mock_stats_class:
            mock_stats_instance = MagicMock()
            mock_stats_instance.sort_stats = MagicMock()
            mock_stats_instance.print_stats = MagicMock()
            mock_stats_class.return_value = mock_stats_instance
            
            # Create a string stream with predictable content
            import io
            mock_stream = io.StringIO("Test Stats Output")
            mock_stats_class.return_value.stream = mock_stream
            
            # We need to mock the actual pstats.Stats to return our mock
            with patch('utils.profiler.cProfile.Profile'):
                output_file = tmp_path / "test_report.md"
                save_profile_results(mock_profiler, 10.0, output_file)
                
                assert output_file.exists()
                content = output_file.read_text()
                assert "Pipeline Runtime Profile Report" in content
                assert "Total Runtime" in content
                assert "Test Stats Output" in content

    def test_save_profile_results_pass_threshold(self, tmp_path):
        """Test PASS status when under 15 mins."""
        mock_profiler = MagicMock()
        with patch('utils.profiler.pstats.Stats') as mock_stats_class:
            mock_stats_instance = MagicMock()
            mock_stats_instance.sort_stats = MagicMock()
            mock_stats_instance.print_stats = MagicMock()
            mock_stats_class.return_value = mock_stats_instance
            
            import io
            mock_stream = io.StringIO("Stats")
            mock_stats_class.return_value.stream = mock_stream
            
            output_file = tmp_path / "test_report.md"
            # 10 seconds is well under 15 mins
            save_profile_results(mock_profiler, 10.0, output_file)
            
            content = output_file.read_text()
            assert "**Status**: PASS" in content

    def test_save_profile_results_fail_threshold(self, tmp_path):
        """Test FAIL status when over 15 mins."""
        mock_profiler = MagicMock()
        with patch('utils.profiler.pstats.Stats') as mock_stats_class:
            mock_stats_instance = MagicMock()
            mock_stats_instance.sort_stats = MagicMock()
            mock_stats_instance.print_stats = MagicMock()
            mock_stats_class.return_value = mock_stats_instance
            
            import io
            mock_stream = io.StringIO("Stats")
            mock_stats_class.return_value.stream = mock_stream
            
            output_file = tmp_path / "test_report.md"
            # 20 minutes is over 15 mins
            save_profile_results(mock_profiler, 20 * 60, output_file)
            
            content = output_file.read_text()
            assert "**Status**: FAIL" in content
            assert "exceeded the 15-minute limit" in content