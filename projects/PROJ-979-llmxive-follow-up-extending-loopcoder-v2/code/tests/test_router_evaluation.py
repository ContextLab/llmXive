"""
Unit tests for router evaluation logic (T020).

Tests:
- Accuracy calculation
- Random baseline calculation
- Paired t-test implementation
- Bootstrap significance test
- End-to-end evaluation flow
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.router_evaluation import (
    calculate_accuracy,
    calculate_random_baseline_accuracy,
    paired_ttest_router_vs_baseline,
    bootstrap_significance_test,
    evaluate_router,
    align_data
)

class TestAccuracyCalculations:
    """Tests for accuracy calculation functions."""

    def test_calculate_accuracy_perfect_match(self):
        """Test accuracy when predictions perfectly match ground truth."""
        ground_truth = [1, 2, 3, 1, 2]
        predictions = [1, 2, 3, 1, 2]
        
        accuracy = calculate_accuracy(ground_truth, predictions)
        assert accuracy == 1.0

    def test_calculate_accuracy_no_match(self):
        """Test accuracy when predictions never match ground truth."""
        ground_truth = [1, 2, 3, 1, 2]
        predictions = [2, 3, 1, 2, 3]
        
        accuracy = calculate_accuracy(ground_truth, predictions)
        assert accuracy == 0.0

    def test_calculate_accuracy_partial_match(self):
        """Test accuracy with partial matches."""
        ground_truth = [1, 2, 3, 1, 2]
        predictions = [1, 3, 3, 2, 2]  # 3 matches out of 5
        
        accuracy = calculate_accuracy(ground_truth, predictions)
        assert accuracy == 0.6

    def test_calculate_random_baseline_all_k1(self):
        """Test random baseline when all ground truth is k=1."""
        ground_truth = [1, 1, 1, 1]
        
        baseline_acc = calculate_random_baseline_accuracy(ground_truth)
        assert baseline_acc == 1.0

    def test_calculate_random_baseline_no_k1(self):
        """Test random baseline when no ground truth is k=1."""
        ground_truth = [2, 3, 4, 2]
        
        baseline_acc = calculate_random_baseline_accuracy(ground_truth)
        assert baseline_acc == 0.0

    def test_calculate_random_baseline_mixed(self):
        """Test random baseline with mixed ground truth."""
        ground_truth = [1, 2, 1, 3, 1]  # 3 out of 5 are k=1
        
        baseline_acc = calculate_random_baseline_accuracy(ground_truth)
        assert baseline_acc == 0.6

    def test_calculate_random_baseline_empty(self):
        """Test random baseline with empty ground truth."""
        ground_truth = []
        
        baseline_acc = calculate_random_baseline_accuracy(ground_truth)
        assert baseline_acc == 0.0

class TestStatisticalTests:
    """Tests for statistical significance testing functions."""

    def test_paired_ttest_router_better(self):
        """Test t-test when router is significantly better."""
        # Create data where router is always correct, baseline is 50% correct
        ground_truth = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2] * 10  # 50% k=1
        router_predictions = ground_truth  # Always correct
        
        t_stat, p_value = paired_ttest_router_vs_baseline(ground_truth, router_predictions)
        
        # Router accuracy = 1.0, Baseline accuracy = 0.5
        # Difference should be significant
        assert p_value < 0.05
        assert t_stat > 0  # Router should have higher mean

    def test_paired_ttest_equal(self):
        """Test t-test when router and baseline perform equally."""
        # All ground truth is k=1, so both router and baseline should be 100%
        ground_truth = [1] * 100
        router_predictions = [1] * 100
        
        t_stat, p_value = paired_ttest_router_vs_baseline(ground_truth, router_predictions)
        
        # No difference expected
        assert abs(t_stat) < 1e-6
        assert p_value > 0.05

    def test_bootstrap_test_significant(self):
        """Test bootstrap test when router is significantly better."""
        ground_truth = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2] * 20
        router_predictions = ground_truth  # Perfect router
        
        p_value = bootstrap_significance_test(ground_truth, router_predictions, n_iterations=1000)
        
        # Should be highly significant
        assert p_value < 0.05

    def test_bootstrap_test_not_significant(self):
        """Test bootstrap test when router is not better than baseline."""
        # Create data where router performs same as baseline
        ground_truth = [1] * 100  # All k=1
        router_predictions = [1] * 100  # Router also predicts all k=1
        
        p_value = bootstrap_significance_test(ground_truth, router_predictions, n_iterations=1000)
        
        # No difference expected
        assert p_value > 0.05

class TestAlignData:
    """Tests for data alignment function."""

    def test_align_data_basic(self):
        """Test basic alignment of ground truth and predictions."""
        convergence_data = [
            {'task_id': 'A', 'optimal_k': 1},
            {'task_id': 'B', 'optimal_k': 2},
            {'task_id': 'C', 'optimal_k': 3}
        ]
        router_data = [
            {'task_id': 'A', 'predicted_k': 1},
            {'task_id': 'B', 'predicted_k': 2},
            {'task_id': 'C', 'predicted_k': 3}
        ]
        
        gt_list, pred_list = align_data(convergence_data, router_data)
        
        assert gt_list == [1, 2, 3]
        assert pred_list == [1, 2, 3]

    def test_align_data_unordered(self):
        """Test alignment when data is not in the same order."""
        convergence_data = [
            {'task_id': 'C', 'optimal_k': 3},
            {'task_id': 'A', 'optimal_k': 1},
            {'task_id': 'B', 'optimal_k': 2}
        ]
        router_data = [
            {'task_id': 'B', 'predicted_k': 2},
            {'task_id': 'C', 'predicted_k': 3},
            {'task_id': 'A', 'predicted_k': 1}
        ]
        
        gt_list, pred_list = align_data(convergence_data, router_data)
        
        # Should be sorted by task_id
        assert gt_list == [1, 2, 3]
        assert pred_list == [1, 2, 3]

    def test_align_data_partial_overlap(self):
        """Test alignment when there's partial overlap."""
        convergence_data = [
            {'task_id': 'A', 'optimal_k': 1},
            {'task_id': 'B', 'optimal_k': 2},
            {'task_id': 'C', 'optimal_k': 3}
        ]
        router_data = [
            {'task_id': 'B', 'predicted_k': 2},
            {'task_id': 'D', 'predicted_k': 1}  # D not in convergence
        ]
        
        gt_list, pred_list = align_data(convergence_data, router_data)
        
        # Only B should be in the result
        assert len(gt_list) == 1
        assert gt_list == [2]
        assert pred_list == [2]

    def test_align_data_no_overlap(self):
        """Test alignment when there's no overlap."""
        convergence_data = [
            {'task_id': 'A', 'optimal_k': 1}
        ]
        router_data = [
            {'task_id': 'B', 'predicted_k': 2}
        ]
        
        with pytest.raises(ValueError, match="No common task_ids"):
            align_data(convergence_data, router_data)

class TestEvaluateRouter:
    """Tests for the main evaluate_router function."""

    def test_evaluate_router_full_flow(self):
        """Test complete evaluation flow with mock data."""
        ground_truth = [1, 2, 1, 3, 1, 2, 1, 2, 1, 1] * 10  # 60% k=1
        router_predictions = [1, 2, 1, 3, 1, 2, 1, 2, 1, 1] * 10  # Perfect router
        
        results = evaluate_router(ground_truth, router_predictions)
        
        assert results['router_accuracy'] == 1.0
        assert results['baseline_accuracy'] == 0.6
        assert results['accuracy_improvement'] == 0.4
        assert results['sample_size'] == 100
        assert results['is_significant'] == True
        assert results['p_value'] < 0.05

    def test_evaluate_router_worse_than_baseline(self):
        """Test evaluation when router performs worse than baseline."""
        # All k=1, so baseline is 100%
        # Router predicts everything as k=2
        ground_truth = [1] * 100
        router_predictions = [2] * 100
        
        results = evaluate_router(ground_truth, router_predictions)
        
        assert results['router_accuracy'] == 0.0
        assert results['baseline_accuracy'] == 1.0
        assert results['accuracy_improvement'] == -1.0
        assert results['is_significant'] == False  # Router is significantly worse, but we test for better

    def test_evaluate_router_bootstrap(self):
        """Test evaluation using bootstrap method."""
        ground_truth = [1, 2, 1, 2, 1, 2, 1, 2, 1, 2] * 20
        router_predictions = ground_truth  # Perfect router
        
        results = evaluate_router(
            ground_truth, 
            router_predictions, 
            use_bootstrap=True, 
            bootstrap_iterations=500
        )
        
        assert results['statistical_test'] == 'bootstrap'
        assert results['is_significant'] == True
        assert results['p_value'] < 0.05

class TestIntegration:
    """Integration tests for the router evaluation module."""

    def test_end_to_end_with_temp_files(self):
        """Test end-to-end flow with temporary files."""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            # Create mock data files
            convergence_file = Path(temp_dir) / "convergence_results.csv"
            predictions_file = Path(temp_dir) / "router_predictions.csv"
            results_file = Path(temp_dir) / "evaluation_results.json"
            
            # Write mock data
            with open(convergence_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['task_id', 'optimal_k', 'converged'])
                writer.writeheader()
                for i in range(100):
                    writer.writerow({
                        'task_id': f'task_{i}',
                        'optimal_k': 1 if i % 2 == 0 else 2,
                        'converged': 'True'
                    })
            
            with open(predictions_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['task_id', 'predicted_k', 'confidence'])
                writer.writeheader()
                for i in range(100):
                    writer.writerow({
                        'task_id': f'task_{i}',
                        'predicted_k': 1 if i % 2 == 0 else 2,  # Perfect predictions
                        'confidence': 0.9
                    })
            
            # Mock the file paths
            with patch('src.router_evaluation.CONVERGENCE_RESULTS_PATH', convergence_file), \
                 patch('src.router_evaluation.ROUTER_PREDICTIONS_PATH', predictions_file), \
                 patch('src.router_evaluation.EVALUATION_RESULTS_PATH', results_file):
                
                    # Import and run main
                    import importlib
                    import src.router_evaluation as router_eval_module
                    importlib.reload(router_eval_module)
                    
                    router_eval_module.main()
                    
                    # Check results file
                    assert results_file.exists()
                    
                    with open(results_file, 'r') as f:
                        results = json.load(f)
                    
                    assert results['router_accuracy'] == 1.0
                    assert results['baseline_accuracy'] == 0.5
                    assert results['is_significant'] == True
        
        finally:
            shutil.rmtree(temp_dir)