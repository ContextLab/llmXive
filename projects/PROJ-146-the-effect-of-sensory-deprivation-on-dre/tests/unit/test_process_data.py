import pytest
import pandas as pd
import numpy as np
import os
import yaml
import tempfile
import shutil

from process_data import load_protocol, derive_condition_column, save_processed_data, process_data_for_threshold

@pytest.fixture
def sample_protocol():
    return {
        "strict_threshold_label": "strict (complete isolation)",
        "moderate_threshold_label": "moderate (partial sensory reduction)",
        "partial_threshold_label": "partial (minimal sensory reduction)",
        "N": 200
    }

@pytest.fixture
def sample_dataframe():
    n = 10
    df = pd.DataFrame({
        'participant_id': range(n),
        'deprivation_intensity': [0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.0],
        'recall': [0, 0, 1, 1, 1, 0, 1, 1, 1, 0],
        'bizarreness': [3, 4, 5, 6, 2, 3, 7, 6, 5, 4]
    })
    return df

@pytest.fixture
def temp_dir():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

def test_load_protocol_success(sample_protocol, temp_dir):
    protocol_path = os.path.join(temp_dir, "protocol.yaml")
    with open(protocol_path, 'w') as f:
        yaml.dump(sample_protocol, f)
    
    result = load_protocol(protocol_path)
    assert result == sample_protocol

def test_derive_condition_strict(sample_dataframe, sample_protocol):
    # Strict cutoff is 0.8
    result = derive_condition_column(sample_dataframe, sample_protocol, 'strict')
    
    # Check that condition column exists
    assert 'condition' in result.columns
    
    # Check specific assignments
    # 0.9 and 0.95 should be "strict (complete isolation)"
    # Others should be "control"
    strict_label = sample_protocol['strict_threshold_label']
    
    assert result.loc[result['deprivation_intensity'] == 0.9, 'condition'].iloc[0] == strict_label
    assert result.loc[result['deprivation_intensity'] == 0.95, 'condition'].iloc[0] == strict_label
    assert result.loc[result['deprivation_intensity'] == 0.1, 'condition'].iloc[0] == "control"

def test_derive_condition_partial(sample_dataframe, sample_protocol):
    # Partial cutoff is 0.2
    result = derive_condition_column(sample_dataframe, sample_protocol, 'partial')
    
    partial_label = sample_protocol['partial_threshold_label']
    
    # 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95 should be partial_label
    # 0.1, 0.2, 0.0 should be control
    assert result.loc[result['deprivation_intensity'] == 0.3, 'condition'].iloc[0] == partial_label
    assert result.loc[result['deprivation_intensity'] == 0.2, 'condition'].iloc[0] == "control"

def test_save_processed_data(sample_dataframe, temp_dir):
    output_path = os.path.join(temp_dir, "test_output.csv")
    save_processed_data(sample_dataframe, output_path)
    
    assert os.path.exists(output_path)
    loaded = pd.read_csv(output_path)
    assert len(loaded) == len(sample_dataframe)

def test_process_data_for_threshold(sample_dataframe, sample_protocol, temp_dir):
    input_path = os.path.join(temp_dir, "input.csv")
    sample_dataframe.to_csv(input_path, index=False)
    
    output_path = os.path.join(temp_dir, "output.csv")
    
    process_data_for_threshold(input_path, sample_protocol, 'moderate', output_path)
    
    assert os.path.exists(output_path)
    result = pd.read_csv(output_path)
    assert 'condition' in result.columns
    assert result['condition'].dtype == object # Strings

def test_invalid_threshold_type(sample_dataframe, sample_protocol):
    with pytest.raises(ValueError):
        derive_condition_column(sample_dataframe, sample_protocol, 'invalid')