"""
Unit tests for the evaluator module.

Tests for Pearson correlation calculation, MAE calculation,
and evaluation result handling.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import json

from src.services.evaluator import (
    EvaluationResult,
    calculate_pearson_correlation,
    calculate_mae,
    evaluate_predictions,
    save_evaluation_results,
    run_evaluation
)


class TestCalculatePearsonCorrelation:
    """Tests for Pearson correlation coefficient calculation."""
    
    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data."""
        predictions = [1.0, 2.0, 3.0, 4.0, 5.0]
        actuals = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        r = calculate_pearson_correlation(predictions, actuals)
        assert np.isclose(r, 1.0, atol=1e-10)
    
    def test_perfect_negative_correlation(self):
        """Test with perfectly negatively correlated data."""
        predictions = [1.0, 2.0, 3.0, 4.0, 5.0]
        actuals = [5.0, 4.0, 3.0, 2.0, 1.0]
        
        r = calculate_pearson_correlation(predictions, actuals)
        assert np.isclose(r, -1.0, atol=1e-10)
    
    def test_no_correlation(self):
        """Test with uncorrelated data."""
        predictions = [1.0, 2.0, 3.0, 4.0, 5.0]
        actuals = [3.0, 1.0, 4.0, 1.0, 5.0]
        
        r = calculate_pearson_correlation(predictions, actuals)
        # Should not be exactly 0, but should be low
        assert abs(r) < 0.9
    
    def test_empty_lists(self):
        """Test with empty lists raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            calculate_pearson_correlation([], [])
    
    def test_different_lengths(self):
        """Test with different length lists raises ValueError."""
        with pytest.raises(ValueError, match="must have same length"):
            calculate_pearson_correlation([1.0, 2.0], [1.0])
    
    def test_single_value(self):
        """Test with single value - correlation undefined."""
        predictions = [1.0]
        actuals = [1.0]
        
        # With single value, standard deviation is 0, so correlation is undefined
        # scipy returns NaN in this case
        r = calculate_pearson_correlation(predictions, actuals)
        assert np.isnan(r)
    
    def test_constant_values(self):
        """Test with constant values - correlation undefined."""
        predictions = [1.0, 1.0, 1.0]
        actuals = [1.0, 1.0, 1.0]
        
        r = calculate_pearson_correlation(predictions, actuals)
        assert np.isnan(r)

class TestCalculateMAE:
    """Tests for Mean Absolute Error calculation."""
    
    def test_perfect_predictions(self):
        """Test with perfect predictions (MAE = 0)."""
        predictions = [1.0, 2.0, 3.0, 4.0, 5.0]
        actuals = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        mae = calculate_mae(predictions, actuals)
        assert mae == 0.0
    
    def test_simple_mae(self):
        """Test with simple case."""
        predictions = [1.0, 2.0, 3.0]
        actuals = [1.5, 2.5, 3.5]
        
        # Errors: 0.5, 0.5, 0.5 -> MAE = 0.5
        mae = calculate_mae(predictions, actuals)
        assert mae == 0.5
    
    def test_empty_lists(self):
        """Test with empty lists raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            calculate_mae([], [])
    
    def test_different_lengths(self):
        """Test with different length lists raises ValueError."""
        with pytest.raises(ValueError, match="must have same length"):
            calculate_mae([1.0, 2.0], [1.0])
    
    def test_negative_errors(self):
        """Test that negative errors are handled correctly (absolute value)."""
        predictions = [1.0, 2.0, 3.0]
        actuals = [2.0, 3.0, 4.0]
        
        # Errors: -1, -1, -1 -> |errors|: 1, 1, 1 -> MAE = 1
        mae = calculate_mae(predictions, actuals)
        assert mae == 1.0

class TestEvaluationResult:
    """Tests for EvaluationResult class."""
    
    def test_create_result(self):
        """Test creating an EvaluationResult."""
        result = EvaluationResult(
            pearson_r=0.85,
            mae=0.12,
            num_samples=100
        )
        
        assert result.pearson_r == 0.85
        assert result.mae == 0.12
        assert result.num_samples == 100
        assert result.predictions is None
        assert result.actuals is None
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        predictions = [1.0, 2.0, 3.0]
        actuals = [1.1, 2.1, 3.1]
        
        result = EvaluationResult(
            pearson_r=0.95,
            mae=0.1,
            num_samples=3,
            predictions=predictions,
            actuals=actuals
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["pearson_r"] == 0.95
        assert result_dict["mae"] == 0.1
        assert result_dict["num_samples"] == 3
        assert result_dict["predictions"] == predictions
        assert result_dict["actuals"] == actuals
    
    def test_repr(self):
        """Test string representation."""
        result = EvaluationResult(
            pearson_r=0.85,
            mae=0.12,
            num_samples=100
        )
        
        repr_str = repr(result)
        assert "pearson_r=0.8500" in repr_str
        assert "mae=0.1200" in repr_str
        assert "num_samples=100" in repr_str

class TestEvaluatePredictions:
    """Tests for the main evaluation function."""
    
    def test_evaluate_simple(self):
        """Test evaluation with simple data."""
        predictions = [1.0, 2.0, 3.0, 4.0, 5.0]
        actuals = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        result = evaluate_predictions(predictions, actuals)
        
        assert result.pearson_r == 1.0
        assert result.mae == 0.0
        assert result.num_samples == 5
    
    def test_evaluate_with_noise(self):
        """Test evaluation with noisy data."""
        predictions = [1.0, 2.0, 3.0, 4.0, 5.0]
        actuals = [1.1, 1.9, 3.2, 3.8, 5.1]
        
        result = evaluate_predictions(predictions, actuals)
        
        # Should have high correlation but non-zero MAE
        assert result.pearson_r > 0.9
        assert result.mae > 0.0
        assert result.num_samples == 5
    
    def test_evaluate_empty(self):
        """Test evaluation with empty list raises error."""
        with pytest.raises(ValueError, match="empty prediction list"):
            evaluate_predictions([], [])

class TestSaveEvaluationResults:
    """Tests for saving evaluation results."""
    
    def test_save_and_load(self):
        """Test saving results to JSON and loading back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.json"
            
            result = EvaluationResult(
                pearson_r=0.85,
                mae=0.12,
                num_samples=100,
                predictions=[1.0, 2.0],
                actuals=[1.1, 2.1]
            )
            
            save_evaluation_results(result, output_path)
            
            # Verify file exists
            assert output_path.exists()
            
            # Load and verify content
            with open(output_path, 'r') as f:
                loaded_dict = json.load(f)
            
            assert loaded_dict["pearson_r"] == 0.85
            assert loaded_dict["mae"] == 0.12
            assert loaded_dict["num_samples"] == 100
            assert loaded_dict["predictions"] == [1.0, 2.0]
            assert loaded_dict["actuals"] == [1.1, 2.1]

class TestRunEvaluation:
    """Tests for the run_evaluation function."""
    
    def test_run_evaluation_no_save(self):
        """Test running evaluation without saving."""
        predictions = [1.0, 2.0, 3.0]
        actuals = [1.0, 2.0, 3.0]
        
        result = run_evaluation(predictions, actuals)
        
        assert result.pearson_r == 1.0
        assert result.mae == 0.0
    
    def test_run_evaluation_with_save(self):
        """Test running evaluation with saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.json"
            
            predictions = [1.0, 2.0, 3.0]
            actuals = [1.0, 2.0, 3.0]
            
            result = run_evaluation(predictions, actuals, output_path)
            
            assert output_path.exists()
            assert result.pearson_r == 1.0
            assert result.mae == 0.0