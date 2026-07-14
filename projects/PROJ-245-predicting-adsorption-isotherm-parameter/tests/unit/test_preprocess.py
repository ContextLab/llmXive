"""
Unit tests for code/data/preprocess.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import json

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.preprocess import (
    filter_type_isotherms,
    remove_missing_targets,
    normalize_units,
    handle_missing_pore_volume,
    preprocess_pipeline
)


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    data = {
        'material_id': ['M1', 'M2', 'M3', 'M4', 'M5'],
        'isotherm_type': ['I', 'II', 'I', '1', 'IV'],
        'polarizability': [1.0, 2.0, 3.0, 4.0, 5.0],
        'langmuir_capacity': [10.0, 20.0, np.nan, 40.0, 50.0],
        'henry_constant': [100.0, 200.0, 300.0, np.nan, 500.0],
        'surface_area': [1000.0, 2000.0, 3000.0, 4000.0, 5000.0],
        'pore_volume': [0.1, 0.2, np.nan, 0.4, 0.5]
    }
    return pd.DataFrame(data)


def test_filter_type_isotherms(sample_df):
    """Test filtering for Type I isotherms."""
    df_filtered, count = filter_type_isotherms(sample_df)
    
    # Should keep M1 (I), M3 (I), M4 (1)
    # Should remove M2 (II), M5 (IV)
    assert len(df_filtered) == 3
    assert count == 2
    assert set(df_filtered['material_id']) == {'M1', 'M3', 'M4'}


def test_remove_missing_targets(sample_df):
    """Test removing rows with missing target values."""
    df_clean, count = remove_missing_targets(sample_df)
    
    # Should remove M3 (missing langmuir) and M4 (missing henry)
    # Should keep M1, M2, M5
    assert len(df_clean) == 3
    assert count == 2
    assert set(df_clean['material_id']) == {'M1', 'M2', 'M5'}


def test_handle_missing_pore_volume_exclude(sample_df):
    """Test excluding rows with missing pore volume."""
    df_clean, log = handle_missing_pore_volume(sample_df, impute_method='exclude')
    
    # Should remove M3 (missing pore_volume)
    assert len(df_clean) == 4
    assert log['rows_excluded'] == 1
    assert log['rows_imputed'] == 0


def test_handle_missing_pore_volume_impute(sample_df):
    """Test imputing missing pore volume with median."""
    df_clean, log = handle_missing_pore_volume(sample_df, impute_method='median')
    
    # Should keep all 5 rows, impute M3
    assert len(df_clean) == 5
    assert log['rows_imputed'] == 1
    assert log['rows_excluded'] == 0
    # Check that M3's pore_volume is the median of non-missing values (0.1, 0.2, 0.4, 0.5) -> 0.3
    m3_pore = df_clean[df_clean['material_id'] == 'M3']['pore_volume'].values[0]
    assert np.isclose(m3_pore, 0.3)


def test_preprocess_pipeline(tmp_path):
    """Test the full preprocessing pipeline."""
    # Create input file
    input_path = tmp_path / "input.csv"
    data = {
        'material_id': ['M1', 'M2', 'M3'],
        'isotherm_type': ['I', 'II', 'I'],
        'polarizability': [1.0, 2.0, 3.0],
        'langmuir_capacity': [10.0, 20.0, 30.0],
        'henry_constant': [100.0, 200.0, 300.0],
        'surface_area': [1000.0, 2000.0, 3000.0],
        'pore_volume': [0.1, np.nan, 0.3]
    }
    pd.DataFrame(data).to_csv(input_path, index=False)
    
    output_path = tmp_path / "output.csv"
    
    result = preprocess_pipeline(
        input_path=str(input_path),
        output_path=str(output_path),
        impute_pore_volume='median'
    )
    
    assert result['output_rows'] == 2  # M2 removed (not Type I)
    assert output_path.exists()
    df_output = pd.read_csv(output_path)
    assert 'material_id' in df_output.columns
    assert 'polarizability' in df_output.columns
    assert 'pore_volume' in df_output.columns