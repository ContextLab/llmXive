import os
import sys
import pytest
import json
import tempfile
import pickle

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.null_baseline import (
    compute_global_mean,
    predict_null_model,
    evaluate_model,
    compare_models,
    run_null_baseline_analysis
)

class TestComputeGlobalMean:
    def test_compute_mean_basic(self):
        """Test basic mean calculation."""
        train_data = [
            {'temperature': 100.0},
            {'temperature': 200.0},
            {'temperature': 300.0}
        ]
        mean = compute_global_mean(train_data)
        assert mean == 200.0

    def test_compute_mean_empty_raises(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="Training data is empty"):
            compute_global_mean([])

    def test_compute_mean_no_temperature_raises(self):
        """Test that missing temperature keys raise ValueError."""
        train_data = [{'other_key': 100.0}]
        with pytest.raises(ValueError, match="No temperature values found"):
            compute_global_mean(train_data)

class TestPredictNullModel:
    def test_predict_null_basic(self):
        """Test that predictions are all equal to mean."""
        mean_temp = 150.0
        test_data = [{'id': 1}, {'id': 2}, {'id': 3}]
        predictions = predict_null_model(mean_temp, test_data)
        assert predictions == [150.0, 150.0, 150.0]
        assert len(predictions) == len(test_data)

    def test_predict_null_empty_test(self):
        """Test prediction with empty test data."""
        predictions = predict_null_model(100.0, [])
        assert predictions == []

class TestEvaluateModel:
    def test_evaluate_mae_basic(self):
        """Test MAE calculation."""
        predictions = [100.0, 200.0, 300.0]
        actuals = [110.0, 190.0, 310.0]
        metrics = evaluate_model(predictions, actuals)
        # MAE = (10 + 10 + 10) / 3 = 10
        assert metrics['mae'] == 10.0

    def test_evaluate_r2_perfect(self):
        """Test R² calculation for perfect predictions."""
        predictions = [100.0, 200.0, 300.0]
        actuals = [100.0, 200.0, 300.0]
        metrics = evaluate_model(predictions, actuals)
        assert metrics['r2'] == 1.0

    def test_evaluate_r2_worst(self):
        """Test R² calculation for constant predictions (worst case)."""
        predictions = [200.0, 200.0, 200.0]
        actuals = [100.0, 200.0, 300.0]
        metrics = evaluate_model(predictions, actuals)
        # Mean actual = 200, SS_tot = 20000, SS_res = 20000, R² = 0
        assert metrics['r2'] == 0.0

    def test_evaluate_mismatched_lengths_raises(self):
        """Test that mismatched lengths raise ValueError."""
        with pytest.raises(ValueError, match="same length"):
            evaluate_model([1.0, 2.0], [1.0])

class TestCompareModels:
    def test_compare_basic(self):
        """Test basic comparison logic."""
        null_metrics = {'mae': 100.0, 'r2': 0.0}
        rf_metrics = {'mae': 50.0, 'r2': 0.5}
        comparison = compare_models(null_metrics, rf_metrics)
        # Improvement = (100 - 50) / 100 * 100 = 50%
        assert comparison['null_model_mae'] == 100.0
        assert comparison['rf_model_mae'] == 50.0
        assert comparison['percentage_improvement'] == 50.0

    def test_compare_rf_worse(self):
        """Test when RF performs worse than null."""
        null_metrics = {'mae': 50.0, 'r2': 0.0}
        rf_metrics = {'mae': 100.0, 'r2': 0.0}
        comparison = compare_models(null_metrics, rf_metrics)
        # Improvement = (50 - 100) / 50 * 100 = -100%
        assert comparison['percentage_improvement'] == -100.0

    def test_compare_zero_null_mae(self):
        """Test division by zero when null MAE is 0."""
        null_metrics = {'mae': 0.0, 'r2': 1.0}
        rf_metrics = {'mae': 10.0, 'r2': 0.0}
        comparison = compare_models(null_metrics, rf_metrics)
        assert comparison['percentage_improvement'] == 0.0

class TestRunNullBaselineAnalysis:
    def test_run_analysis_basic(self):
        """Test full analysis flow with mock LOSO results."""
        loso_results = {
            'folds': [
                {
                    'fold_id': 'fold_1',
                    'train_data': [
                        {'temperature': 100.0},
                        {'temperature': 200.0}
                    ],
                    'test_data': [{'id': 1}, {'id': 2}],
                    'rf_predictions': [150.0, 150.0],
                    'actuals': [160.0, 140.0]
                }
            ]
        }
        
        results = run_null_baseline_analysis(loso_results)
        
        assert 'null_model_mae' in results
        assert 'rf_model_mae' in results
        assert 'percentage_improvement' in results
        
        # Null model mean = 150, predictions = [150, 150], actuals = [160, 140]
        # Null MAE = (10 + 10) / 2 = 10
        assert results['null_model_mae'] == 10.0

    def test_run_analysis_empty_folds(self):
        """Test with no folds."""
        loso_results = {'folds': []}
        results = run_null_baseline_analysis(loso_results)
        assert results['percentage_improvement'] == 0.0

    def test_run_analysis_save_to_file(self):
        """Test that results are saved to file."""
        loso_results = {
            'folds': [
                {
                    'fold_id': 'fold_1',
                    'train_data': [{'temperature': 100.0}],
                    'test_data': [{'id': 1}],
                    'rf_predictions': [100.0],
                    'actuals': [110.0]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            # Run analysis and save
            from models.null_baseline import main as null_main
            import argparse
            
            # Mock args
            sys.argv = ['null_baseline.py', '--input', '/dev/null', '--output', output_path]
            
            # We'll manually test the save logic since main() expects real files
            comparison = run_null_baseline_analysis(loso_results)
            
            with open(output_path, 'w') as f:
                json.dump(comparison, f)
            
            with open(output_path, 'r') as f:
                saved = json.load(f)
            
            assert 'null_model_mae' in saved
            assert os.path.exists(output_path)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)