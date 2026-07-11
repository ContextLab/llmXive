"""
Unit tests for the serialization module (T025).
"""
import os
import json
import tempfile
import pytest
import pandas as pd
from io import StringIO

# Import the function to test
# Note: In the real project structure, this would be:
# from code.serialize_results import serialize_model_results
# But for the test runner context, we assume the path is set up correctly or use relative imports if needed.
# Since we are implementing the file, we assume the import path works as per standard project layout.
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from serialize_results import serialize_model_results, serialize_sensitivity_results

def test_serialize_model_results_creates_file():
    """Test that serialization creates a valid JSON file with correct structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock data
        mock_df = pd.DataFrame({
            'term': ['Intercept', 'X'],
            'coef': [1.0, 2.0],
            'std err': [0.1, 0.2],
            'P>|z|': [0.05, 0.01],
            'df_resid': [100, 100]
        })

        output_path = serialize_model_results(
            model_name="test_model",
            results_df=mock_df,
            output_dir=tmpdir
        )

        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data['model_name'] == "test_model"
        assert data['framing'] == "associational"
        assert len(data['results']) == 2
        assert data['results'][0]['term'] == 'Intercept'
        assert abs(data['results'][0]['estimate'] - 1.0) < 0.001
        assert data['results'][0]['p_value'] == 0.05

def test_serialize_sensitivity_results():
    """Test sensitivity results serialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sensitivity_data = {
            "strict": {"odds_ratio": 1.5, "p_value": 0.01},
            "moderate": {"odds_ratio": 1.2, "p_value": 0.05}
        }
        
        output_path = serialize_sensitivity_results(
            threshold_results=sensitivity_data,
            output_dir=tmpdir,
            filename="test_sensitivity.json"
        )

        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data['analysis_type'] == "sensitivity_threshold_sweep"
        assert 'strict' in data['thresholds']
        assert data['thresholds']['strict']['odds_ratio'] == 1.5

def test_handles_missing_columns_gracefully():
    """Test that missing columns in DataFrame don't crash the serializer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # DataFrame with missing 'std err' column
        mock_df = pd.DataFrame({
            'term': ['Intercept'],
            'coef': [1.0],
            'P>|z|': [0.05]
            # 'std err' is missing
        })

        output_path = serialize_model_results(
            model_name="test_missing",
            results_df=mock_df,
            output_dir=tmpdir
        )

        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Should default to 0.0 for missing std err
        assert data['results'][0]['std_error'] == 0.0