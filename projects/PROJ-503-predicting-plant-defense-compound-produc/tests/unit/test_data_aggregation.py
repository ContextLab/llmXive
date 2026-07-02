"""
Unit tests for data aggregation functionality.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the module to test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_aggregation import (
    extract_condition_key,
    aggregate_by_condition,
    calculate_pairing_rate,
    update_pairing_report
)

@pytest.fixture
def sample_expression_data():
    """Create sample expression data for testing."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'condition': ['control', 'control', 'treatment', 'treatment', 'treatment'],
        'treatment': ['none', 'none', 'herbivore', 'herbivore', 'herbivore'],
        'time_point': ['0h', '0h', '24h', '24h', '48h'],
        'gene1': [10.5, 11.2, 15.3, 14.8, 16.1],
        'gene2': [5.2, 5.8, 8.1, 7.9, 8.5],
        'gene3': [2.1, 2.3, 3.5, 3.2, 3.8]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_metabolite_data():
    """Create sample metabolite data for testing."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'condition': ['control', 'control', 'treatment', 'treatment', 'treatment'],
        'treatment': ['none', 'none', 'herbivore', 'herbivore', 'herbivore'],
        'time_point': ['0h', '0h', '24h', '24h', '48h'],
        'metabolite1': [100.5, 102.3, 150.2, 148.7, 155.1],
        'metabolite2': [50.2, 52.1, 80.3, 78.9, 82.5]
    }
    return pd.DataFrame(data)

def test_extract_condition_key():
    """Test condition key extraction."""
    row = pd.Series({
        'condition': 'control',
        'treatment': 'none',
        'time_point': '0h'
    })
    
    key = extract_condition_key(row, ['condition', 'treatment', 'time_point'])
    assert key == 'control_none_0h'
    
    # Test with missing columns
    key = extract_condition_key(row, ['condition', 'missing_col'])
    assert key == 'control_'

def test_aggregate_by_condition(sample_expression_data):
    """Test aggregation by experimental condition."""
    condition_cols = ['condition', 'treatment', 'time_point']
    
    aggregated = aggregate_by_condition(
        sample_expression_data,
        condition_cols,
        sample_id_col='sample_id'
    )
    
    # Should have 3 unique conditions
    assert len(aggregated) == 3
    
    # Check that numeric columns are averaged
    assert 'gene1' in aggregated.columns
    assert 'gene2' in aggregated.columns
    
    # Verify aggregation logic
    control_group = aggregated[aggregated['condition'] == 'control']
    assert len(control_group) == 1
    
    # Original control samples: S1 (10.5), S2 (11.2)
    # Expected average: (10.5 + 11.2) / 2 = 10.85
    assert abs(control_group['gene1'].iloc[0] - 10.85) < 0.01

def test_aggregate_by_condition_empty_dataframe():
    """Test aggregation with empty DataFrame."""
    empty_df = pd.DataFrame()
    
    with pytest.warns(UserWarning):
        result = aggregate_by_condition(
            empty_df,
            ['condition'],
            sample_id_col='sample_id'
        )
    
    assert result.empty

def test_aggregate_by_condition_missing_columns(sample_expression_data):
    """Test aggregation when some condition columns are missing."""
    condition_cols = ['condition', 'nonexistent_col', 'time_point']
    
    # Should handle missing columns gracefully
    aggregated = aggregate_by_condition(
        sample_expression_data,
        condition_cols,
        sample_id_col='sample_id'
    )
    
    # Should still aggregate successfully
    assert len(aggregated) > 0

def test_calculate_pairing_rate(sample_expression_data, sample_metabolite_data):
    """Test pairing rate calculation."""
    # Perfect pairing
    rate = calculate_pairing_rate(
        sample_expression_data,
        sample_metabolite_data,
        sample_id_col='sample_id'
    )
    assert rate == 1.0
    
    # Partial pairing
    partial_metab = sample_metabolite_data.iloc[:3]
    rate = calculate_pairing_rate(
        sample_expression_data,
        partial_metab,
        sample_id_col='sample_id'
    )
    # 3 paired out of 5 total unique samples
    assert rate == 3/5

def test_calculate_pairing_rate_no_overlap():
    """Test pairing rate with no overlap."""
    expr_df = pd.DataFrame({'sample_id': ['S1', 'S2']})
    metab_df = pd.DataFrame({'sample_id': ['S3', 'S4']})
    
    rate = calculate_pairing_rate(expr_df, metab_df, sample_id_col='sample_id')
    assert rate == 0.0

def test_update_pairing_report():
    """Test pairing report update functionality."""
    original_report = {
        'pairing_rate': 0.85,
        'status': 'failed',
        'details': 'Original report'
    }
    
    updated = update_pairing_report(
        original_report,
        original_rate=0.85,
        aggregated_expression_count=10,
        aggregated_metabolite_count=8,
        pairing_rate_after_aggregation=0.92
    )
    
    assert 'aggregation_fallback' in updated
    assert updated['aggregation_fallback']['attempted'] is True
    assert updated['aggregation_fallback']['status'] == 'insufficient'
    assert updated['final_pairing_rate'] == 0.92

def test_update_pairing_report_success():
    """Test pairing report update when aggregation succeeds."""
    original_report = {
        'pairing_rate': 0.85,
        'status': 'failed'
    }
    
    updated = update_pairing_report(
        original_report,
        original_rate=0.85,
        aggregated_expression_count=10,
        aggregated_metabolite_count=10,
        pairing_rate_after_aggregation=0.96
    )
    
    assert updated['status'] == 'passed_after_aggregation'
    assert updated['aggregation_fallback']['status'] == 'completed'

def test_aggregate_preserves_categorical_data(sample_expression_data):
    """Test that categorical data is preserved during aggregation."""
    condition_cols = ['condition', 'treatment']
    
    aggregated = aggregate_by_condition(
        sample_expression_data,
        condition_cols,
        sample_id_col='sample_id'
    )
    
    # Check that categorical columns are preserved
    assert 'condition' in aggregated.columns
    assert 'treatment' in aggregated.columns
    
    # Verify that categorical values are taken from first occurrence
    control_row = aggregated[aggregated['condition'] == 'control'].iloc[0]
    assert control_row['condition'] == 'control'
    assert control_row['treatment'] == 'none'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])