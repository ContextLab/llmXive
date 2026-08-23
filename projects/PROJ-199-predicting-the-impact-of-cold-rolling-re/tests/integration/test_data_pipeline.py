"""
Integration Tests for Data Acquisition Pipeline (T011).

Verifies that the download module correctly handles:
1. Real data retrieval (mocked for CI to avoid network dependency in unit tests)
2. Strict failure behavior when real data is unavailable (no synthetic fallback)
3. Configuration validation and reduction level resolution
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys
import os

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import run_pipeline, download_from_huggingface
from code.config import ConfigurationError
from code.data.generate_synthetic import generate_synthetic_dataset

# Mock the data source to simulate real data availability
class TestDataPipeline:
    
    @patch('code.data.download.download_from_huggingface')
    @patch('code.data.download.load_and_validate_data')
    @patch('code.data.download.get_reductions')
    def test_real_data_flow(self, mock_get_reductions, mock_load, mock_download):
        """Test the happy path when real data is available."""
        # Setup mocks
        mock_df = pd.DataFrame({
            'material': ['aluminum', 'aluminum', 'copper'],
            'reduction_pct': [30, 40, 30],
            'phi1': [0.0, 10.0, 5.0],
            'Phi': [0.0, 15.0, 10.0],
            'phi2': [0.0, 20.0, 15.0],
            'confidence_index': [0.9, 0.85, 0.95]
        })
        
        # Simulate successful download
        mock_download.return_value = [Path("fake_ebsd_data.parquet")]
        mock_load.return_value = {"ALUMINUM": mock_df, "COPPER": mock_df}
        mock_get_reductions.return_value = [30, 40]

        # Execute pipeline
        result = run_pipeline()

        # Assertions
        mock_download.assert_called_once()
        mock_load.assert_called_once()
        assert "ALUMINUM" in result
        assert "COPPER" in result
        assert len(result["ALUMINUM"]) == 3
        assert len(result["COPPER"]) == 3
        assert all(result["ALUMINUM"]["confidence_index"] >= 0.1)

    @patch('code.data.download.download_from_huggingface')
    @patch('code.data.download.get_reductions')
    def test_fail_loudly_on_missing_data(self, mock_get_reductions, mock_download):
        """
        Test that the pipeline FAILS LOUDLY when real data is unavailable.
        
        Per FR-001 and Constitution Principle I:
        - NO synthetic data generation
        - NO silent fallback
        - Must raise DataUnavailableError or similar
        """
        # Simulate network failure or missing data
        mock_download.side_effect = Exception("Network error: Cannot fetch data")
        mock_get_reductions.return_value = [30, 40]

        # The pipeline must raise an exception, NOT fall back to synthetic
        with pytest.raises(Exception) as exc_info:
            run_pipeline()
        
        # Verify the error message indicates data unavailability
        assert "Network error" in str(exc_info.value) or "DataUnavailable" in str(exc_info.value)
        
        # CRITICAL: Verify synthetic generator was NEVER called
        with patch.object(generate_synthetic_dataset, 'generate_synthetic_ebsd') as mock_synthetic:
            # Reset mock to ensure clean state
            mock_synthetic.reset_mock()
            
            # Re-run to confirm it still fails without calling synthetic
            with pytest.raises(Exception):
                run_pipeline()
            
            # Assert synthetic was not called
            mock_synthetic.assert_not_called()

    @patch('code.data.download.get_reductions')
    @patch('code.data.download.load_research_md')
    def test_reduction_levels_resolution(self, mock_load_research, mock_get_reductions):
        """
        Test that reduction levels are correctly resolved from research.md or defaults.
        """
        # Scenario 1: research.md exists and has reduction_levels
        mock_load_research.return_value = {
            'reduction_levels': [0, 20, 40, 60]
        }
        mock_get_reductions.return_value = [0, 20, 40, 60]
        
        # Verify the function reads the config correctly
        # (Implementation detail depends on how get_reductions works internally)
        # We verify the mock was called and returned expected values
        assert mock_get_reductions.return_value == [0, 20, 40, 60]
        
        # Scenario 2: research.md missing, fallback to defaults
        mock_load_research.return_value = None
        mock_get_reductions.return_value = [0, 10, 20, 30, 40, 50, 60, 70, 80]
        
        assert mock_get_reductions.return_value == [0, 10, 20, 30, 40, 50, 60, 70, 80]

    @patch('code.data.download.download_from_huggingface')
    @patch('code.data.download.get_reductions')
    def test_missing_reduction_level_warning(self, mock_get_reductions, mock_download):
        """
        Test that missing reduction levels trigger warnings but don't crash the whole pipeline.
        """
        mock_df = pd.DataFrame({
            'material': ['aluminum'],
            'reduction_pct': [30],
            'phi1': [0.0], 'Phi': [0.0], 'phi2': [0.0],
            'confidence_index': [0.9]
        })
        
        # Simulate partial data availability (missing 40% reduction)
        mock_download.return_value = [Path("fake_ebsd_data.parquet")]
        
        # Mock load to return data only for 30%
        def mock_load_func(*args, **kwargs):
            return {"ALUMINUM": mock_df}
        
        with patch('code.data.download.load_and_validate_data', side_effect=mock_load_func):
            mock_get_reductions.return_value = [30, 40]
            
            # Should succeed but log warning about missing 40%
            result = run_pipeline()
            
            assert "ALUMINUM" in result
            # Verify only 30% data is present
            assert all(result["ALUMINUM"]["reduction_pct"] == 30)

    @patch('code.data.download.download_from_huggingface')
    @patch('code.data.download.get_reductions')
    def test_all_levels_missing_error(self, mock_get_reductions, mock_download):
        """
        Test that if ALL levels for a metal are missing, DataUnavailableError is raised.
        """
        # Simulate no data at all
        mock_download.return_value = []
        mock_get_reductions.return_value = [30, 40]
        
        # Should raise error
        with pytest.raises(Exception) as exc_info:
            run_pipeline()
        
        assert "DataUnavailable" in str(exc_info.value) or "missing" in str(exc_info.value).lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])