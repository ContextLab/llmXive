import os
import sys
import json
import tempfile
import pandas as pd
import pytest

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from preprocess import detect_outcome_type

def test_detect_binary_outcome():
    """Test detection of binary outcome type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "outcome.json")
        
        # Create binary data (2 unique values)
        df = pd.DataFrame({
            'risk_taking_score': [0, 1, 0, 1, 1, 0],
            'participant_id': [1, 2, 3, 4, 5, 6]
        })
        df.to_csv(input_path, index=False)
        
        detect_outcome_type(input_path, output_path)
        
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert result['type'] == 'binary'

def test_detect_continuous_outcome():
    """Test detection of continuous outcome type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "outcome.json")
        
        # Create continuous data (15 unique values)
        df = pd.DataFrame({
            'risk_taking_score': list(range(15)),
            'participant_id': list(range(15))
        })
        df.to_csv(input_path, index=False)
        
        detect_outcome_type(input_path, output_path)
        
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert result['type'] == 'continuous'

def test_missing_column():
    """Test that missing column raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.csv")
        output_path = os.path.join(tmpdir, "outcome.json")
        
        # Create data without required column
        df = pd.DataFrame({
            'other_col': [1, 2, 3]
        })
        df.to_csv(input_path, index=False)
        
        with pytest.raises(ValueError, match="Column 'risk_taking_score' not found"):
            detect_outcome_type(input_path, output_path)