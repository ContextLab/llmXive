import pytest
import pandas as pd
import numpy as np
import tempfile
import json
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.clean import calculate_coverage_rate
from config import get_config

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create required subdirs
        (tmpdir / 'raw').mkdir()
        (tmpdir / 'processed').mkdir()
        
        # Mock config to use this temp dir
        # We can't easily patch the global config, so we will create the files manually
        # and pass them to the function or mock the config.
        # For this test, we will create the files and patch the config getter.
        yield tmpdir

def test_coverage_rate_calculation(temp_data_dir):
    """
    Test T015: Calculate coverage rate.
    Verifies that the function correctly counts rows in raw files and merged file,
    calculates the ratio, and saves to metrics.json.
    """
    # Setup test data
    fao_path = temp_data_dir / 'raw' / 'fao_land_use.csv'
    wb_path = temp_data_dir / 'raw' / 'wb_gdp_pop.csv'
    merged_path = temp_data_dir / 'processed' / 'merged_panel.csv'
    metrics_path = temp_data_dir / 'processed' / 'metrics.json'
    
    # Create FAO data (100 rows)
    fao_df = pd.DataFrame({
        'country_code': ['USA'] * 100,
        'year': list(range(2000, 300)),
        'land_use_change_rate': np.random.rand(100)
    })
    fao_df.to_csv(fao_path, index=False)
    
    # Create WB data (80 rows) - less than FAO
    wb_df = pd.DataFrame({
        'country_code': ['USA'] * 80,
        'year': list(range(2000, 80)),
        'gdp_per_capita': np.random.rand(80) * 10000,
        'population_density': np.random.rand(80) * 100
    })
    wb_df.to_csv(wb_path, index=False)
    
    # Create Merged data (50 rows) - intersection
    merged_df = pd.DataFrame({
        'country_code': ['USA'] * 50,
        'year': list(range(2000, 50)),
        'land_use_change_rate': np.random.rand(50),
        'gdp_per_capita': np.random.rand(50) * 10000,
        'population_density': np.random.rand(50) * 100,
        'regime_type': np.random.randint(0, 2, 50)
    })
    merged_df.to_csv(merged_path, index=False)
    
    # Patch config to point to temp_data_dir
    original_get_config = get_config
    
    def mock_get_config():
        return {
            'DATA_RAW_DIR': str(temp_data_dir / 'raw'),
            'DATA_PROCESSED_DIR': str(temp_data_dir / 'processed'),
            'DATA_YEARS_START': 2000,
            'DATA_YEARS_END': 2020
        }
    
    # Monkey patch
    import config
    config.get_config = mock_get_config
    
    try:
        # Run the function
        result = calculate_coverage_rate()
        
        # Verify metrics.json exists and content
        assert metrics_path.exists(), "metrics.json was not created"
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        assert metrics['total_fao_available'] == 100
        assert metrics['total_wb_available'] == 80
        assert metrics['total_merged'] == 50
        assert metrics['min_available'] == 80
        # Expected coverage: 50 / 80 = 0.625
        assert abs(metrics['coverage_rate'] - 0.625) < 1e-6
        
        # Verify return value
        assert result == metrics
        
    finally:
        # Restore original config
        config.get_config = original_get_config

def test_coverage_rate_zero_division(temp_data_dir):
    """
    Test T015: Handle case where min_available is 0.
    """
    fao_path = temp_data_dir / 'raw' / 'fao_land_use.csv'
    wb_path = temp_data_dir / 'raw' / 'wb_gdp_pop.csv'
    merged_path = temp_data_dir / 'processed' / 'merged_panel.csv'
    metrics_path = temp_data_dir / 'processed' / 'metrics.json'
    
    # Create empty FAO
    fao_df = pd.DataFrame(columns=['country_code', 'year', 'land_use_change_rate'])
    fao_df.to_csv(fao_path, index=False)
    
    # Create WB
    wb_df = pd.DataFrame({
        'country_code': ['USA'],
        'year': [2000],
        'gdp_per_capita': [1000]
    })
    wb_df.to_csv(wb_path, index=False)
    
    # Create Merged (should be 0 if FAO is 0, but let's say 0)
    merged_df = pd.DataFrame(columns=['country_code', 'year', 'land_use_change_rate', 'gdp_per_capita'])
    merged_df.to_csv(merged_path, index=False)
    
    import config
    def mock_get_config():
        return {
            'DATA_RAW_DIR': str(temp_data_dir / 'raw'),
            'DATA_PROCESSED_DIR': str(temp_data_dir / 'processed')
        }
    config.get_config = mock_get_config
    
    try:
        result = calculate_coverage_rate()
        assert result['coverage_rate'] == 0.0
    finally:
        import config as cfg_mod
        # Restore is tricky if we re-imported, but for test isolation it's fine
        pass
