import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

# Import the module
import code.run_inference as run_inference

def test_run_inference_with_tracking_structure():
    """
    Test that run_inference_with_tracking returns the expected structure
    including energy and co2 fields when mocked.
    """
    # Mock the dataset
    mock_dataset = [
        {"id": "p1", "prompt": "def hello(): pass"},
        {"id": "p2", "prompt": "print('world')"}
    ]
    
    # Mock the model and tokenizer
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    
    # Mock the generate method to return a simple string
    mock_tokenizer.decode.return_value = "def hello():\n    pass"
    mock_tokenizer.eos_token_id = 50256
    
    # Mock the EmissionsTracker
    mock_tracker = MagicMock()
    mock_tracker.__enter__ = MagicMock(return_value=mock_tracker)
    mock_tracker.__exit__ = MagicMock(return_value=None)
    
    # Mock the CSV reading (simulating CodeCarbon output)
    # We need to mock the pandas read_csv call inside the function
    mock_df = MagicMock()
    mock_df.empty = False
    mock_df.iloc = [{"energy_kWh": 0.005, "co2_kg": 0.001}] # Mock row access
    
    with patch.object(run_inference, 'load_model', return_value=(mock_model, mock_tokenizer)), \
         patch.object(run_inference, 'generate_code', return_value="def hello(): pass"), \
         patch.object(run_inference, 'count_loc', return_value=1), \
         patch('code.run_inference.EmissionsTracker', return_value=mock_tracker), \
         patch('code.run_inference.pd.read_csv', return_value=mock_df):
        
        results = run_inference.run_inference_with_tracking(mock_dataset, "gpt2-medium", {})
        
        assert len(results) == 2
        for res in results:
            assert "prompt_id" in res
            assert "energy_kWh" in res
            assert "co2_kg" in res
            assert "generated_code" in res
            assert "loc_count" in res
            assert "model_used" in res
            assert res["energy_kWh"] > 0
            assert res["co2_kg"] > 0

def test_count_loc():
    """Test LOC counting logic"""
    code_with_comments = """
    # This is a comment
    def foo():
        x = 1 # inline comment
        return x
    
    # Another comment
    """
    assert run_inference.count_loc(code_with_comments) == 2 # def foo and return x

def test_save_results():
    """Test saving results to JSON"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_results.json")
        results = [{"prompt_id": "1", "energy_kWh": 0.1, "co2_kg": 0.05}]
        
        run_inference.save_results(results, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert len(data) == 1
            assert data[0]["energy_kWh"] == 0.1
