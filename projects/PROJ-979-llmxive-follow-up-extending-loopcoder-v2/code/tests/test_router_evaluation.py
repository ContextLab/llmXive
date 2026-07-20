import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.router_evaluation import (
    load_convergence_results,
    load_router_predictions,
    align_data,
    calculate_accuracy,
    calculate_random_baseline_accuracy,
    paired_ttest_router_vs_baseline,
    bootstrap_significance_test,
    evaluate_router,
    save_evaluation_results,
    print_evaluation_summary
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def sample_convergence_data(temp_dir):
    """Create sample convergence data file."""
    data = [
        {'task_id': 'task_1', 'convergence_step': 2, 'k': 2},
        {'task_id': 'task_2', 'convergence_step': 3, 'k': 3},
        {'task_id': 'task_3', 'convergence_step': 1, 'k': 1},
        {'task_id': 'task_4', 'convergence_step': 4, 'k': 4},
        {'task_id': 'task_5', 'convergence_step': 2, 'k': 2},
    ]
    filepath = os.path.join(temp_dir, 'convergence_results.csv')
    with open(filepath, 'w') as f:
        f.write('task_id,convergence_step,k\n')
        for row in data:
            f.write(f"{row['task_id']},{row['convergence_step']},{row['k']}\n")
    return filepath

@pytest.fixture
def sample_router_predictions(temp_dir):
    """Create sample router predictions file."""
    data = [
        {'task_id': 'task_1', 'predicted_k': 2, 'actual_k': 2, 'entropy': 0.5, 'difficulty': 'easy'},
        {'task_id': 'task_2', 'predicted_k': 3, 'actual_k': 3, 'entropy': 0.8, 'difficulty': 'medium'},
        {'task_id': 'task_3', 'predicted_k': 1, 'actual_k': 1, 'entropy': 0.2, 'difficulty': 'hard'},
        {'task_id': 'task_4', 'predicted_k': 3, 'actual_k': 4, 'entropy': 0.9, 'difficulty': 'medium'},
        {'task_id': 'task_5', 'predicted_k': 2, 'actual_k': 2, 'entropy': 0.4, 'difficulty': 'easy'},
    ]
    filepath = os.path.join(temp_dir, 'router_predictions.csv')
    with open(filepath, 'w') as f:
        f.write('task_id,predicted_k,actual_k,entropy,difficulty\n')
        for row in data:
            f.write(f"{row['task_id']},{row['predicted_k']},{row['actual_k']},{row['entropy']},{row['difficulty']}\n")
    return filepath

class TestAccuracyCalculations:
    def test_calculate_accuracy_perfect(self):
        """Test accuracy calculation with perfect predictions."""
        data = [
            {'predicted_k': 2, 'actual_k': 2},
            {'predicted_k': 3, 'actual_k': 3},
            {'predicted_k': 1, 'actual_k': 1},
        ]
        accuracy = calculate_accuracy(data)
        assert accuracy == 1.0

    def test_calculate_accuracy_partial(self):
        """Test accuracy calculation with partial predictions."""
        data = [
            {'predicted_k': 2, 'actual_k': 2},  # Correct
            {'predicted_k': 3, 'actual_k': 4},  # Within tolerance (1)
            {'predicted_k': 1, 'actual_k': 4},  # Outside tolerance
        ]
        accuracy = calculate_accuracy(data, tolerance=1)
        assert accuracy == 2/3

    def test_calculate_accuracy_empty(self):
        """Test accuracy calculation with empty data."""
        accuracy = calculate_accuracy([])
        assert accuracy == 0.0

    def test_calculate_random_baseline_accuracy(self):
        """Test random baseline accuracy calculation."""
        data = [
            {'actual_k': 1},  # Correct for baseline
            {'actual_k': 2},  # Incorrect
            {'actual_k': 1},  # Correct for baseline
        ]
        accuracy = calculate_random_baseline_accuracy(data)
        assert accuracy == 2/3

    def test_calculate_random_baseline_accuracy_empty(self):
        """Test random baseline accuracy with empty data."""
        accuracy = calculate_random_baseline_accuracy([])
        assert accuracy == 0.0

class TestStatisticalTests:
    def test_paired_ttest_basic(self):
        """Test paired t-test with simple data."""
        router_acc = [1, 1, 0, 1, 1]
        baseline_acc = [1, 0, 0, 1, 0]
        t_stat, p_val = paired_ttest_router_vs_baseline(router_acc, baseline_acc)
        assert not np.isnan(t_stat)
        assert 0 <= p_val <= 1

    def test_paired_ttest_unequal_lengths(self):
        """Test paired t-test with unequal lengths raises error."""
        router_acc = [1, 1, 0]
        baseline_acc = [1, 0]
        with pytest.raises(ValueError):
            paired_ttest_router_vs_baseline(router_acc, baseline_acc)

    def test_bootstrap_significance_test(self):
        """Test bootstrap significance test."""
        router_acc = [1, 1, 0, 1, 1, 1, 0, 1]
        baseline_acc = [1, 0, 0, 1, 0, 1, 0, 1]
        mean_diff, p_val, is_significant = bootstrap_significance_test(
            router_acc, baseline_acc, n_iterations=100
        )
        assert isinstance(mean_diff, float)
        assert 0 <= p_val <= 1
        assert isinstance(is_significant, bool)

    def test_bootstrap_significance_test_unequal_lengths(self):
        """Test bootstrap significance test with unequal lengths raises error."""
        router_acc = [1, 1, 0]
        baseline_acc = [1, 0]
        with pytest.raises(ValueError):
            bootstrap_significance_test(router_acc, baseline_acc)

class TestAlignData:
    def test_align_data_success(self, temp_dir, sample_convergence_data, sample_router_predictions):
        """Test successful data alignment."""
        conv_results = load_convergence_results(sample_convergence_data)
        router_preds = load_router_predictions(sample_router_predictions)
        
        aligned = align_data(conv_results, router_preds)
        
        assert len(aligned) == 5
        assert all('task_id' in item for item in aligned)
        assert all('convergence_step' in item for item in aligned)
        assert all('predicted_k' in item for item in aligned)

    def test_align_data_missing_predictions(self, temp_dir):
        """Test alignment when some predictions are missing."""
        conv_data = [
            {'task_id': 'task_1', 'convergence_step': 2, 'k': 2},
            {'task_id': 'task_2', 'convergence_step': 3, 'k': 3},
        ]
        pred_data = [
            {'task_id': 'task_1', 'predicted_k': 2, 'actual_k': 2, 'entropy': 0.5, 'difficulty': 'easy'},
        ]
        
        filepath_conv = os.path.join(temp_dir, 'conv.csv')
        filepath_pred = os.path.join(temp_dir, 'pred.csv')
        
        with open(filepath_conv, 'w') as f:
            f.write('task_id,convergence_step,k\n')
            for row in conv_data:
                f.write(f"{row['task_id']},{row['convergence_step']},{row['k']}\n")
        
        with open(filepath_pred, 'w') as f:
            f.write('task_id,predicted_k,actual_k,entropy,difficulty\n')
            for row in pred_data:
                f.write(f"{row['task_id']},{row['predicted_k']},{row['actual_k']},{row['entropy']},{row['difficulty']}\n")
        
        conv_results = load_convergence_results(filepath_conv)
        router_preds = load_router_predictions(filepath_pred)
        
        aligned = align_data(conv_results, router_preds)
        
        assert len(aligned) == 1
        assert aligned[0]['task_id'] == 'task_1'

class TestEvaluateRouter:
    def test_evaluate_router_full(self, temp_dir, sample_convergence_data, sample_router_predictions):
        """Test full router evaluation."""
        conv_results = load_convergence_results(sample_convergence_data)
        router_preds = load_router_predictions(sample_router_predictions)
        
        aligned = align_data(conv_results, router_preds)
        results = evaluate_router(aligned)
        
        assert 'router_accuracy' in results
        assert 'baseline_accuracy' in results
        assert 'accuracy_improvement' in results
        assert 't_statistic' in results
        assert 'p_value_ttest' in results
        assert 'is_significant' in results
        assert results['n_samples'] == 5

class TestIntegration:
    def test_save_evaluation_results(self, temp_dir, sample_convergence_data, sample_router_predictions):
        """Test saving evaluation results to JSON."""
        conv_results = load_convergence_results(sample_convergence_data)
        router_preds = load_router_predictions(sample_router_predictions)
        
        aligned = align_data(conv_results, router_preds)
        results = evaluate_router(aligned)
        
        output_file = os.path.join(temp_dir, 'evaluation_results.json')
        save_evaluation_results(results, output_file)
        
        assert os.path.exists(output_file)
        
        with open(output_file, 'r') as f:
            loaded_results = json.load(f)
        
        assert loaded_results == results

    def test_print_evaluation_summary(self, temp_dir, sample_convergence_data, sample_router_predictions, capsys):
        """Test printing evaluation summary."""
        conv_results = load_convergence_results(sample_convergence_data)
        router_preds = load_router_predictions(sample_router_predictions)
        
        aligned = align_data(conv_results, router_preds)
        results = evaluate_router(aligned)
        
        print_evaluation_summary(results)
        
        captured = capsys.readouterr()
        assert "ROUTER EVALUATION SUMMARY" in captured.out
        assert "Router Accuracy:" in captured.out
        assert "Baseline Accuracy:" in captured.out
        assert "Significant" in captured.out