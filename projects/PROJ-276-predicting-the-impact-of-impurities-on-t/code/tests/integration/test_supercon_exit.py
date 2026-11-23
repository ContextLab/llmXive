import pytest
import sys
import os
import tempfile
from pathlib import Path
import pandas as pd
from unittest.mock import patch, MagicMock

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.unit.data.synthetic_nulls import create_test_nulls_df

class TestSuperConExitCode:
    """Test that download_supercon.py exits with code 1 when >50% entries lack impurities."""

    def test_exit_code_on_high_null_impurity(self, tmp_path):
        """
        Verify that the script exits with code 1 when the dataset has >50%
        entries without impurity columns.
        """
        # Create a synthetic dataframe with >50% missing impurity data
        # This simulates the condition described in T013
        df = create_test_nulls_df()
        
        # Mock load_dataset to return our synthetic data
        with patch('src.ingestion.download_supercon.load_dataset') as mock_load:
            # Create a mock dataset object that converts to our dataframe
            mock_dataset = MagicMock()
            mock_dataset.to_pandas.return_value = df
            mock_load.return_value = mock_dataset

            # Mock the output paths to use temp directory
            with patch('src.ingestion.download_supercon.get_project_root') as mock_root:
                mock_root.return_value = tmp_path
                
                # Mock the directory creation
                with patch('pathlib.Path.mkdir') as mock_mkdir:
                    mock_mkdir.return_value = None
                    
                    # Run the main function
                    from src.ingestion.download_supercon import main
                    
                    # We expect sys.exit(1) to be called
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    assert exc_info.value.code == 1

    def test_success_on_valid_impurity_coverage(self, tmp_path):
        """
        Verify that the script succeeds (returns 0) when impurity coverage is valid.
        """
        # Create a valid dataframe with sufficient impurity data
        valid_df = pd.DataFrame({
            'Tc': [39.0, 40.0, 38.5],
            'impurity_C': [0.01, 0.02, 0.015],
            'impurity_O': [0.0, 0.01, 0.005],
            'temp_K': [20.0, 25.0, 30.0],
            'pressure_GPa': [0.0, 0.0, 0.0],
            'source': ['synthetic', 'synthetic', 'synthetic']
        })
        
        with patch('src.ingestion.download_supercon.load_dataset') as mock_load:
            mock_dataset = MagicMock()
            mock_dataset.to_pandas.return_value = valid_df
            mock_load.return_value = mock_dataset

            with patch('src.ingestion.download_supercon.get_project_root') as mock_root:
                mock_root.return_value = tmp_path
                
                with patch('pathlib.Path.mkdir') as mock_mkdir:
                    mock_mkdir.return_value = None
                    
                    with patch('src.ingestion.download_supercon.attach_provenance_header'):
                        from src.ingestion.download_supercon import main
                        
                        # Should return 0 on success
                        result = main()
                        assert result == 0
