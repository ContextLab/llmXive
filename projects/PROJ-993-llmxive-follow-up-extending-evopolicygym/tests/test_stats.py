import pytest
import json
import os
import tempfile
import pandas as pd
from code.analysis.stats import run_mixed_effects_model

def test_mixed_effects_model_output():
    """
    Integration test for mixed-effects model analysis outputting p-value and effect size.
    """
    # Create a temporary CSV file with mock data
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        data = {
            'score': [10, 12, 11, 20, 22, 21, 15, 16, 14, 25, 26, 24],
            'condition': ['baseline', 'baseline', 'baseline', 'counterfactual', 'counterfactual', 'counterfactual',
                          'baseline', 'baseline', 'baseline', 'counterfactual', 'counterfactual', 'counterfactual'],
            'complexity': [1.0, 1.1, 1.2, 2.0, 2.1, 2.2, 1.5, 1.6, 1.4, 2.5, 2.6, 2.4],
            'seed': [1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2],
            'run_id': [1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3]
        }
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        temp_csv_path = f.name
    
    temp_json_path = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json').name
    
    try:
        results = run_mixed_effects_model(temp_csv_path, temp_json_path)
        
        # Verify the output structure
        assert 'p_value_condition' in results
        assert 'coef_condition' in results
        assert 'significant' in results
        assert 'formula' in results
        
        # Verify the conditional logic
        # Since we have mock data, we just check the logic is applied
        assert isinstance(results['significant'], bool)
        
        # Verify JSON file was written
        assert os.path.exists(temp_json_path)
        with open(temp_json_path, 'r') as f:
            loaded_results = json.load(f)
            assert loaded_results == results
            
    finally:
        # Cleanup
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)
        if os.path.exists(temp_json_path):
            os.remove(temp_json_path)

def test_mixed_effects_model_missing_data():
    """
    Test that the model fails loudly if input data is missing.
    """
    with pytest.raises(FileNotFoundError):
        run_mixed_effects_model("non_existent_file.csv", "output.json")

def test_mixed_effects_model_invalid_columns():
    """
    Test that the model fails if required columns are missing.
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        data = {
            'score': [10, 12],
            'wrong_column': [1, 2]
        }
        df = pd.DataFrame(data)
        df.to_csv(f.name, index=False)
        temp_csv_path = f.name
    
    temp_json_path = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json').name
    
    try:
        with pytest.raises(ValueError):
            run_mixed_effects_model(temp_csv_path, temp_json_path)
    finally:
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)
        if os.path.exists(temp_json_path):
            os.remove(temp_json_path)