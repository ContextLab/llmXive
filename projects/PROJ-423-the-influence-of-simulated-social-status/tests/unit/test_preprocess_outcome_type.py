import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np

# Ensure local imports work
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from preprocess import detect_outcome_type

def test_detect_outcome_type_binary():
    """Test that outcome type is detected as binary when unique values < 10."""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dataframe with binary outcome (2 unique values)
        df = pd.DataFrame({
            'participant_id': range(100),
            'risk_taking_score': np.random.choice([0, 1], size=100)
        })
        
        output_path = os.path.join(tmpdir, "outcome_type.json")
        
        # Call the function
        result = detect_outcome_type(df, output_path)
        
        # Assert result
        assert result == "binary"
        
        # Verify file was written
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data == {"type": "binary"}

def test_detect_outcome_type_continuous():
    """Test that outcome type is detected as continuous when unique values >= 10."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dataframe with continuous outcome (many unique values)
        df = pd.DataFrame({
            'participant_id': range(100),
            'risk_taking_score': np.random.uniform(0, 100, size=100)
        })
        
        output_path = os.path.join(tmpdir, "outcome_type.json")
        
        # Call the function
        result = detect_outcome_type(df, output_path)
        
        # Assert result
        assert result == "continuous"
        
        # Verify file was written
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data == {"type": "continuous"}

def test_detect_outcome_type_missing_column():
    """Test that ValueError is raised if risk_taking_score column is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dataframe without risk_taking_score
        df = pd.DataFrame({
            'participant_id': range(100),
            'other_column': range(100)
        })
        
        output_path = os.path.join(tmpdir, "outcome_type.json")
        
        # Call the function - should raise ValueError
        with pytest.raises(ValueError, match="Column 'risk_taking_score' not found"):
            detect_outcome_type(df, output_path)

def test_detect_outcome_type_boundary():
    """Test boundary case: exactly 10 unique values should be continuous."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dataframe with exactly 10 unique values
        df = pd.DataFrame({
            'participant_id': range(100),
            'risk_taking_score': np.tile(range(10), 10)
        })
        
        output_path = os.path.join(tmpdir, "outcome_type.json")
        
        # Call the function
        result = detect_outcome_type(df, output_path)
        
        # Assert result - 10 is not < 10, so it should be continuous
        assert result == "continuous"
        
        # Verify file was written
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert data == {"type": "continuous"}
