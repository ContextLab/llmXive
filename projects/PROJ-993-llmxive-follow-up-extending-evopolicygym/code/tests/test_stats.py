import pytest
import json
import os
import tempfile
import pandas as pd
from code.analysis.stats import run_mixed_effects_model, calculate_shift_validation

class TestShiftValidation:
    """Tests for the shift validation statistical test (T045)"""

    def test_calculate_shift_validation_creates_output(self):
        """Test that calculate_shift_validation creates the output JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock input data
            input_path = os.path.join(tmpdir, 'shift_metrics.csv')
            output_path = os.path.join(tmpdir, 'shift_validation.json')
            
            data = {
                'env_name': ['env1', 'env2', 'env3', 'env4', 'env5'],
                'agent_id': ['agent1', 'agent1', 'agent1', 'agent1', 'agent1'],
                'pre_shift_metric': [0.9, 0.85, 0.95, 0.88, 0.92],
                'post_shift_metric': [0.6, 0.55, 0.65, 0.58, 0.62]
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)
            
            # Run the validation
            result = calculate_shift_validation(input_path, output_path)
            
            # Verify output file exists
            assert os.path.exists(output_path), "Output JSON file was not created"
            
            # Verify result structure
            assert 'p_value' in result
            assert 'mean_drop' in result
            assert 'std_drop' in result
            assert 'n_observations' in result
            assert 'significant' in result
            
            # Verify values make sense
            assert result['n_observations'] == 5
            assert result['mean_drop'] > 0  # Should show performance drop
            assert isinstance(result['p_value'], float)

    def test_calculate_shift_validation_no_drop(self):
        """Test that validation handles cases with no performance drop"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'shift_metrics.csv')
            output_path = os.path.join(tmpdir, 'shift_validation.json')
            
            # Create data with no drop (post-shift is same as pre-shift)
            data = {
                'env_name': ['env1', 'env2', 'env3'],
                'agent_id': ['agent1', 'agent1', 'agent1'],
                'pre_shift_metric': [0.9, 0.85, 0.95],
                'post_shift_metric': [0.9, 0.85, 0.95]
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)
            
            result = calculate_shift_validation(input_path, output_path)
            
            # Should detect no significant drop
            assert result['mean_drop'] == 0.0
            assert result['significant'] == False
            assert result['p_value'] > 0.05

    def test_calculate_shift_validation_missing_file(self):
        """Test that validation fails loudly when input file is missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'nonexistent.csv')
            output_path = os.path.join(tmpdir, 'shift_validation.json')
            
            with pytest.raises(FileNotFoundError):
                calculate_shift_validation(input_path, output_path)

    def test_calculate_shift_validation_missing_columns(self):
        """Test that validation fails when required columns are missing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'bad_metrics.csv')
            output_path = os.path.join(tmpdir, 'shift_validation.json')
            
            # Create data missing required columns
            data = {
                'env_name': ['env1', 'env2'],
                'other_col': [1, 2]
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)
            
            with pytest.raises(ValueError):
                calculate_shift_validation(input_path, output_path)

def test_radon_integration():
    """Unit test for radon integration calculating cyclomatic complexity"""
    from code.agents.policy_parser import parse_policy_complexity
    import tempfile
    import os

    # Create a simple Python policy file
    policy_code = """
def policy(observation):
    if observation[0] > 0.5:
  return 1
    else:
  return 0
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(policy_code)
        temp_path = f.name

    try:
        result = parse_policy_complexity(temp_path)
        assert 'cyclomatic_complexity' in result
        assert result['cyclomatic_complexity'] >= 2  # At least 2 branches
    finally:
        os.unlink(temp_path)

def test_mixed_effects_model_output():
    """Integration test for mixed-effects model analysis outputting p-value and effect size"""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'evolution_results.csv')
        output_path = os.path.join(tmpdir, 'stats_results.json')
        
        # Create mock evolution data
        data = {
            'seed': [1, 1, 2, 2, 3, 3],
            'run_id': [1, 2, 1, 2, 1, 2],
            'condition': ['baseline', 'counterfactual', 'baseline', 'counterfactual', 'baseline', 'counterfactual'],
            'metric': [0.5, 0.7, 0.55, 0.75, 0.48, 0.72]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        result = run_mixed_effects_model(input_path, output_path)
        
        assert os.path.exists(output_path)
        assert 'p_value' in result
        assert 'effect_size' in result
        assert 'model_formula' in result
        assert isinstance(result['p_value'], float)
        assert isinstance(result['effect_size'], float)