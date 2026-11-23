import os
import json
import tempfile
import pandas as pd
import pytest
from preprocess import detect_data_structure

def test_between_subjects_structure():
    """Test detection of between-subjects design."""
    data = {
        'participant_id': ['P1', 'P2', 'P3', 'P4'],
        'status_level': ['High', 'Low', 'High', 'Low'],
        'risk_taking_score': [10, 20, 15, 25]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'structure.json')
        config = detect_data_structure(df, output_path)
        
        assert config['type'] == 'between-subjects'
        assert config['n_subjects'] == 4
        assert config['model_type'] == 'fixed-effects'
        
        with open(output_path, 'r') as f:
            saved_config = json.load(f)
        assert saved_config == config

def test_within_subjects_structure():
    """Test detection of within-subjects design."""
    data = {
        'participant_id': ['P1', 'P1', 'P2', 'P2'],
        'status_level': ['High', 'Low', 'High', 'Low'],
        'risk_taking_score': [10, 20, 15, 25]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'structure.json')
        config = detect_data_structure(df, output_path)
        
        assert config['type'] == 'within-subjects'
        assert config['n_subjects'] == 2
        assert config['model_type'] == 'mixed-effects'
        
        with open(output_path, 'r') as f:
            saved_config = json.load(f)
        assert saved_config == config

def test_missing_participant_id():
    """Test that ValueError is raised if participant_id is missing."""
    data = {
        'status_level': ['High', 'Low'],
        'risk_taking_score': [10, 20]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'structure.json')
        with pytest.raises(ValueError, match="Input dataframe must contain 'participant_id' column."):
            detect_data_structure(df, output_path)
