import os
import sys
import logging
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
import pandas as pd
import json

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from ingestion import ingest_materials_data, save_raw_data, logger

class TestIngestionPipeline:
    """Integration tests for the full ingestion pipeline."""

    def test_ingest_multiple_sources_with_logging(self):
        """Test ingesting data from multiple sources and verify logging."""
        # Mock data
        mock_oqmd_data = pd.DataFrame({'id': [1, 2], 'value': [10, 20]})
        mock_aflow_data = pd.DataFrame({'id': [3, 4], 'value': [30, 40]})
        
        with patch('ingestion.fetch_oqmd_data', return_value=mock_oqmd_data) as mock_oqmd:
            with patch('ingestion.fetch_aflow_data', return_value=mock_aflow_data) as mock_aflow:
                with patch('ingestion.fetch_materials_project_data', return_value=None) as mock_mp:
                    with patch('ingestion.logger') as mock_logger:
                        # Run ingestion
                        result = ingest_materials_data(
                            oqmd_url="https://example.com/oqmd",
                            aflow_url="https://example.com/aflow"
                        )
                        
                        # Verify all fetch functions were called
                        mock_oqmd.assert_called_once()
                        mock_aflow.assert_called_once()
                        
                        # Verify results
                        assert 'oqmd' in result
                        assert 'aflow' in result
                        assert len(result['oqmd']) == 2
                        assert len(result['aflow']) == 2
                        
                        # Verify logging
                        info_calls = [call for call in mock_logger.info.call_args_list if 'ingestion' in str(call).lower()]
                        assert len(info_calls) >= 2  # At least start and complete logs

    def test_save_raw_data_creates_files(self, tmp_path):
        """Test that save_raw_data creates the expected CSV files."""
        # Mock data
        mock_data = {
            'oqmd': pd.DataFrame({'id': [1, 2], 'value': [10, 20]}),
            'aflow': pd.DataFrame({'id': [3, 4], 'value': [30, 40]})
        }
        
        with patch('ingestion.logger'):
            save_raw_data(mock_data, str(tmp_path))
            
            # Verify files were created
            assert (tmp_path / 'oqmd_raw.csv').exists()
            assert (tmp_path / 'aflow_raw.csv').exists()
            
            # Verify file contents
            oqmd_df = pd.read_csv(tmp_path / 'oqmd_raw.csv')
            aflow_df = pd.read_csv(tmp_path / 'aflow_raw.csv')
            
            assert len(oqmd_df) == 2
            assert len(aflow_df) == 2
            assert list(oqmd_df.columns) == ['id', 'value']

    def test_partial_failure_handling(self):
        """Test that the pipeline continues if one source fails."""
        mock_oqmd_data = pd.DataFrame({'id': [1, 2], 'value': [10, 20]})
        
        with patch('ingestion.fetch_oqmd_data', return_value=mock_oqmd_data) as mock_oqmd:
            with patch('ingestion.fetch_aflow_data', side_effect=Exception("AFLOW API down")) as mock_aflow:
                with patch('ingestion.logger') as mock_logger:
                    result = ingest_materials_data(
                        oqmd_url="https://example.com/oqmd",
                        aflow_url="https://example.com/aflow"
                    )
                    
                    # OQMD should succeed
                    assert result['oqmd'] is not None
                    assert len(result['oqmd']) == 2
                    
                    # AFLOW should be None due to failure
                    assert result['aflow'] is None
                    
                    # Verify error logging for AFLOW
                    error_calls = [call for call in mock_logger.error.call_args_list if 'AFLOW' in str(call)]
                    assert len(error_calls) >= 1
                    
                    # Verify successful logging for OQMD
                    success_calls = [call for call in mock_logger.info.call_args_list if 'OQMD' in str(call)]
                    assert len(success_calls) >= 1

    def test_retry_count_configuration(self):
        """Test that retry count is configurable via environment variables."""
        # This test verifies the configuration logic
        original_retry = os.getenv('INGESTION_RETRY_COUNT')
        
        try:
            # Set a custom retry count
            os.environ['INGESTION_RETRY_COUNT'] = '10'
            
            # Re-import to pick up the new value
            # Note: In a real scenario, we might need to reload the module
            # For this test, we're just verifying the environment variable is read
            from ingestion import DEFAULT_RETRY_COUNT
            assert DEFAULT_RETRY_COUNT == 10
            
        finally:
            # Restore original value
            if original_retry is None:
                del os.environ['INGESTION_RETRY_COUNT']
            else:
                os.environ['INGESTION_RETRY_COUNT'] = original_retry
