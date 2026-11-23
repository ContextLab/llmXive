import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.analysis.regression import fit_model, evaluate_test, run_regression_analysis

class TestRegression:
    @pytest.fixture
    def sample_data(self):
        """Create a small synthetic dataset for testing."""
        np.random.seed(42)
        n = 100
        data = {
            'tolerance_factor': np.random.rand(n),
            'bond_length_variance': np.random.rand(n) * 0.1,
            'octahedral_tilting': np.random.rand(n) * 10,
            'unit_cell_volume': np.random.rand(n) * 100,
            'chemistry_class': np.random.choice(['oxide', 'halide', 'nitride'], n),
            'thermal_conductivity': np.random.rand(n) * 10 + 5
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_fit_model_cv(self, sample_data):
        """Test 5-fold cross-validation fitting."""
        X = sample_data[['tolerance_factor', 'bond_length_variance']]
        y = sample_data['thermal_conductivity']
        
        results = fit_model(X, y, n_folds=5, seed=42)
        
        assert 'cv_scores' in results
        assert 'mean_cv_score' in results
        assert 'std_cv_score' in results
        assert 'model' in results
        assert len(results['cv_scores']) == 5
        assert isinstance(results['mean_cv_score'], float)

    def test_evaluate_test_metrics(self, sample_data):
        """Test evaluation on held-out test set."""
        X = sample_data[['tolerance_factor', 'bond_length_variance']]
        y = sample_data['thermal_conductivity']
        
        # Fit a model first
        fit_res = fit_model(X, y, seed=42)
        
        # Evaluate
        eval_res = evaluate_test(X, y, fit_res['model'], seed=42)
        
        assert 'r2' in eval_res
        assert 'rmse' in eval_res
        assert 'coefficients' in eval_res
        assert 'pass_target' in eval_res
        assert 'test_size' in eval_res
        assert isinstance(eval_res['r2'], float)
        assert isinstance(eval_res['rmse'], float)

    def test_stratified_split(self, sample_data):
        """Test that stratification by chemistry_class works."""
        X = sample_data[['tolerance_factor', 'bond_length_variance']]
        y = sample_data['thermal_conductivity']
        
        fit_res = fit_model(X, y, seed=42)
        
        # Force a split with stratification
        eval_res = evaluate_test(
            X, y, fit_res['model'], 
            stratify_col='chemistry_class', 
            seed=42
        )
        
        assert eval_res['n_train'] + eval_res['n_test'] == len(sample_data)
        # Verify split sizes are roughly correct (20% test)
        assert 0.15 < eval_res['test_size'] < 0.25 or abs(eval_res['n_test'] / len(sample_data) - 0.2) < 0.05

    def test_run_regression_analysis_io(self, sample_data, temp_output_dir):
        """Test the full pipeline function with file I/O."""
        input_path = temp_output_dir / "input.csv"
        output_path = temp_output_dir / "results.json"
        
        sample_data.to_csv(input_path, index=False)
        
        results = run_regression_analysis(
            input_path=input_path,
            output_path=output_path,
            seed=42
        )
        
        assert output_path.exists()
        assert 'cross_validation' in results
        assert 'test_evaluation' in results
        
        # Verify JSON content
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['input_file'] == str(input_path)
        assert 'r2' in saved_data['test_evaluation']
        assert 'rmse' in saved_data['test_evaluation']

    def test_sc003_target_check(self, sample_data):
        """Verify that the pass_target flag reflects R² > 0.5."""
        X = sample_data[['tolerance_factor', 'bond_length_variance']]
        y = sample_data['thermal_conductivity']
        
        fit_res = fit_model(X, y, seed=42)
        eval_res = evaluate_test(X, y, fit_res['model'], seed=42, target_r2=0.5)
        
        # The flag should be boolean
        assert isinstance(eval_res['pass_target'], bool)
        # If R2 > 0.5, pass_target must be True
        if eval_res['r2'] > 0.5:
            assert eval_res['pass_target'] is True
        else:
            assert eval_res['pass_target'] is False
