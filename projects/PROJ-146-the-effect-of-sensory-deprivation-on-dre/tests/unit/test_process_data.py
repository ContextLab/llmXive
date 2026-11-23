import pytest
import pandas as pd
import os
import tempfile
import yaml
from code.process_data import derive_condition_column, save_processed_data, load_protocol

def test_derive_condition_column_strict():
    """Test that condition column is derived correctly with strict thresholds."""
    # Create a mock protocol
    protocol = {
        'strict_threshold_label': "strict (complete isolation)",
        'moderate_threshold_label': "moderate (partial sensory reduction)",
        'partial_threshold_label': "partial (minimal sensory reduction)",
        'strict_threshold_value': 80,
        'moderate_threshold_value': 50
    }
    
    # Create a mock dataframe
    df = pd.DataFrame({
        'deprivation_intensity': [90, 60, 30, 85, 40]
    })
    
    # Derive condition
    result = derive_condition_column(df, protocol)
    
    # Check that 'condition' column exists
    assert 'condition' in result.columns
    
    # Check the values
    expected_conditions = [
        "strict (complete isolation)",
        "moderate (partial sensory reduction)",
        "partial (minimal sensory reduction)",
        "strict (complete isolation)",
        "moderate (partial sensory reduction)"
    ]
    
    assert list(result['condition']) == expected_conditions

def test_derive_condition_column_missing_intensity():
    """Test that derive_condition_column raises an error if intensity column is missing."""
    protocol = {
        'strict_threshold_label': "strict",
        'moderate_threshold_label': "moderate",
        'partial_threshold_label': "partial",
        'strict_threshold_value': 80,
        'moderate_threshold_value': 50
    }
    
    df = pd.DataFrame({
        'other_column': [1, 2, 3]
    })
    
    with pytest.raises(ValueError, match="missing 'deprivation_intensity' column"):
        derive_condition_column(df, protocol)

def test_save_processed_data():
    """Test that save_processed_data creates a CSV file."""
    df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test.csv')
        save_processed_data(df, output_path)
        
        assert os.path.exists(output_path)
        
        # Read back and check
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == 3
        assert list(saved_df.columns) == ['col1', 'col2']

def test_load_protocol():
    """Test that load_protocol loads the protocol correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        protocol_path = os.path.join(tmpdir, 'protocol.yaml')
        protocol_data = {
            'strict_threshold_label': "strict",
            'moderate_threshold_label': "moderate",
            'partial_threshold_label': "partial"
        }
        
        with open(protocol_path, 'w') as f:
            yaml.dump(protocol_data, f)
        
        protocol = load_protocol(protocol_path)
        
        assert protocol['strict_threshold_label'] == "strict"
        assert protocol['moderate_threshold_label'] == "moderate"
        assert protocol['partial_threshold_label'] == "partial"