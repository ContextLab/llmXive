"""
Unit tests for code/data/mapping.py (T011c).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
import os
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.mapping import map_columns, clean_and_log_exclusions
from code.config import DataConfig

class TestMapping:
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'smiles': ['CCO', 'CC(C)C', None, 'CCC', np.nan],
            'rate': [1.0, 2.5, 3.0, None, 5.0],
            'other_col': ['a', 'b', 'c', 'd', 'e']
        })

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    def test_map_columns(self, sample_df):
        """Test that column mapping works correctly."""
        logger = type('Logger', (), {'info': lambda s, x: None, 'warning': lambda s, x: None, 'error': lambda s, x: None})()
        
        result = map_columns(sample_df, logger)
        
        assert 'SMILES' in result.columns
        assert 'rate_constant' in result.columns
        assert 'smiles' not in result.columns
        assert 'rate' not in result.columns
        assert result['SMILES'].iloc[0] == 'CCO'
        assert result['rate_constant'].iloc[0] == 1.0

    def test_clean_and_log_exclusions(self, sample_df, temp_dir):
        """Test that rows with missing data are excluded and logged."""
        # Temporarily override DataConfig paths for this test
        original_processed_path = DataConfig.processed_data_path
        
        # Create a mock config class that returns our temp dir
        class MockConfig:
            processed_data_path = Path(temp_dir)
        
        # Patch the config usage inside the function (or pass paths directly if refactored)
        # For now, we test the logic assuming the path is handled correctly by the function's internal config
        # We need to ensure the function uses our temp dir.
        # Since DataConfig is imported inside the function, we can't easily mock it without refactoring.
        # Instead, we will test the logic by checking the returned dataframe and the file creation.
        
        # To make this test robust, we will mock the DataConfig class temporarily
        import code.data.mapping as mapping_module
        original_config = mapping_module.DataConfig
        
        class TestConfig:
            processed_data_path = Path(temp_dir)
        
        mapping_module.DataConfig = TestConfig
        
        try:
            logger = type('Logger', (), {'info': lambda s, x: None, 'warning': lambda s, x: None, 'error': lambda s, x: None, 'debug': lambda s, x: None})()
            
            df_cleaned, count = clean_and_log_exclusions(sample_df, logger)
            
            # Check that excluded count is correct (2 rows: index 2 and 3)
            assert count == 2
            
            # Check that cleaned dataframe has 3 rows
            assert len(df_cleaned) == 3
            
            # Check that excluded rows are not in cleaned dataframe
            assert df_cleaned['SMILES'].isna().sum() == 0
            assert df_cleaned['rate_constant'].isna().sum() == 0
            
            # Check that exclusion log was created
            exclusion_log_path = Path(temp_dir) / "exclusion_raw.log"
            assert exclusion_log_path.exists()
            
            # Check content of exclusion log
            exclusion_df = pd.read_csv(exclusion_log_path)
            assert len(exclusion_df) == 2
            assert 'missing_smiles' in exclusion_df['reason'].iloc[0] or 'missing_rate_constant' in exclusion_df['reason'].iloc[1]
        
        finally:
            mapping_module.DataConfig = original_config

if __name__ == "__main__":
    pytest.main([__file__, "-v"])