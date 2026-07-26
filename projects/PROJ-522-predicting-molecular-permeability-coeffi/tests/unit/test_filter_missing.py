import pandas as pd
import logging
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add code to path if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from ingestion import filter_missing_permeability, log_missing_data

class TestFilterMissingPermeability:
    
    def test_filter_removes_nan_target(self):
        """Test that rows with NaN in 'target' are removed."""
        data = {
            'smiles': ['CCO', 'CCCO', 'CCCCO', 'CCCCCO'],
            'target': [1.0, float('nan'), 2.0, float('nan')],
            'source_id': ['A', 'B', 'C', 'D']
        }
        df = pd.DataFrame(data)
        
        mock_logger = MagicMock(spec=logging.Logger)
        
        result = filter_missing_permeability(df, mock_logger)
        
        # Should only have rows with valid targets
        assert len(result) == 2
        assert result['target'].isna().sum() == 0
        
        # Verify logging was called
        mock_logger.info.assert_called()

    def test_filter_preserves_valid_targets(self):
        """Test that rows with valid targets are kept."""
        data = {
            'smiles': ['CCO', 'CCCO'],
            'target': [1.0, 2.0],
            'source_id': ['A', 'B']
        }
        df = pd.DataFrame(data)
        
        mock_logger = MagicMock(spec=logging.Logger)
        
        result = filter_missing_permeability(df, mock_logger)
        
        assert len(result) == 2
        assert list(result['smiles']) == ['CCO', 'CCCO']

    def test_log_exclusion_reason(self):
        """Test that the specific log message 'Missing target variable' is emitted."""
        data = {
            'smiles': ['CCO'],
            'target': [float('nan')],
            'source_id': ['A']
        }
        df = pd.DataFrame(data)
        
        mock_logger = MagicMock(spec=logging.Logger)
        
        filter_missing_permeability(df, mock_logger)
        
        # Check that log_missing_data or info was called with the reason
        # The implementation calls log_missing_data which should log the reason
        calls = [str(call) for call in mock_logger.info.call_args_list]
        found_reason = any("Missing target variable" in call for call in calls)
        assert found_reason, "Log message 'Missing target variable' was not found in logs"

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame(columns=['smiles', 'target'])
        mock_logger = MagicMock(spec=logging.Logger)
        
        result = filter_missing_permeability(df, mock_logger)
        
        assert len(result) == 0
        mock_logger.warning.assert_called()
        
    def test_missing_target_column(self):
        """Test handling when target column is missing."""
        df = pd.DataFrame({'smiles': ['CCO']})
        mock_logger = MagicMock(spec=logging.Logger)
        
        result = filter_missing_permeability(df, mock_logger)
        
        # Should return original (or handle gracefully)
        mock_logger.error.assert_called()
        # In current impl, it returns df as is if column missing, but logs error
        # Depending on strictness, this might be adjusted, but for now we test the log
        assert len(result) == 1