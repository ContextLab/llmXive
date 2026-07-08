"""
Unit tests for metrics.py functionality.
Validates schema compliance and metric calculations.
"""
import pytest
import numpy as np
from lib.metrics import (
    precision_recall_f1,
    auc_roc,
    bootstrap_ci,
    bonferroni_correction,
    wilcoxon_signed_rank,
    paired_ttest,
    brier_score,
    evaluate_detection
)

class TestPrecisionRecallF1:
    def test_perfect_prediction(self):
        y_true = np.array([1, 1, 0, 0])
        y_pred = np.array([1, 1, 0, 0])
        metrics = precision_recall_f1(y_true, y_pred)
        assert metrics['precision'] == 1.0
        assert metrics['recall'] == 1.0
        assert metrics['f1'] == 1.0

    def test_no_true_positives(self):
        y_true = np.array([1, 1, 0, 0])
        y_pred = np.array([0, 0, 0, 0])
        metrics = precision_recall_f1(y_true, y_pred)
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1'] == 0.0

    def test_shape_mismatch(self):
        y_true = np.array([1, 1, 0])
        y_pred = np.array([1, 0])
        with pytest.raises(ValueError):
            precision_recall_f1(y_true, y_pred)

    def test_all_negatives(self):
        """Edge case: no positive predictions or true positives."""
        y_true = np.array([0, 0, 0, 0])
        y_pred = np.array([0, 0, 0, 0])
        metrics = precision_recall_f1(y_true, y_pred)
        # Precision is undefined (0/0), should be 0.0
        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1'] == 0.0

class TestAUCROC:
    def test_perfect_separation(self):
        y_true = np.array([0, 0, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.8, 0.9])
        auc = auc_roc(y_true, y_scores)
        assert auc == 1.0

    def test_random_separation(self):
        np.random.seed(42)
        y_true = np.random.choice([0, 1], size=100)
        y_scores = np.random.rand(100)
        auc = auc_roc(y_true, y_scores)
        # Random should be around 0.5, with tolerance
        assert 0.3 < auc < 0.7

    def test_empty_class(self):
        y_true = np.array([0, 0, 0, 0])
        y_scores = np.array([0.1, 0.2, 0.3, 0.4])
        auc = auc_roc(y_true, y_scores)
        assert auc == 0.5  # Undefined, returns 0.5

    def test_single_class_positive(self):
        y_true = np.array([1, 1, 1, 1])
        y_scores = np.array([0.1, 0.2, 0.3, 0.4])
        auc = auc_roc(y_true, y_scores)
        assert auc == 0.5  # Undefined, returns 0.5

class TestBootstrapCI:
    def test_ci_bounds(self):
        data = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        ci = bootstrap_ci(data, confidence_level=0.95, n_bootstrap=1000, seed=42)
        assert ci['lower'] <= ci['mean'] <= ci['upper']
        assert ci['confidence_level'] == 0.95

    def test_empty_input(self):
        with pytest.raises(ValueError):
            bootstrap_ci(np.array([]))

    def test_single_value(self):
        """CI for single value should have zero width."""
        data = np.array([0.5])
        ci = bootstrap_ci(data, confidence_level=0.95, n_bootstrap=100, seed=42)
        assert ci['lower'] == ci['mean'] == ci['upper']

    def test_confidence_levels(self):
        """Test different confidence levels produce different widths."""
        data = np.random.normal(0, 1, 1000)
        ci_95 = bootstrap_ci(data, confidence_level=0.95, n_bootstrap=500, seed=42)
        ci_99 = bootstrap_ci(data, confidence_level=0.99, n_bootstrap=500, seed=42)
        
        # 99% CI should be wider than 95% CI
        width_95 = ci_95['upper'] - ci_95['lower']
        width_99 = ci_99['upper'] - ci_99['lower']
        assert width_99 > width_95

class TestBonferroniCorrection:
    def test_correction_applied(self):
        p_values = [0.01, 0.02, 0.03]
        bonf = bonferroni_correction(p_values, alpha=0.05)
        # Original p=0.01 becomes 0.03, still significant
        assert bonf['adjusted_p_values'][0] == 0.03
        assert bonf['significant'][0] == True
        # Original p=0.03 becomes 0.09, not significant
        assert bonf['significant'][2] == False

    def test_empty_input(self):
        bonf = bonferroni_correction([], alpha=0.05)
        assert bonf['adjusted_p_values'] == []
        assert bonf['significant'] == []

    def test_all_significant(self):
        p_values = [0.001, 0.002, 0.003]
        bonf = bonferroni_correction(p_values, alpha=0.05)
        # All adjusted p-values should be < 0.05
        assert all(bonf['significant'])

    def test_cap_at_one(self):
        """Adjusted p-values should not exceed 1.0."""
        p_values = [0.5, 0.6, 0.7]
        bonf = bonferroni_correction(p_values, alpha=0.05)
        assert all(p <= 1.0 for p in bonf['adjusted_p_values'])

class TestStatisticalTests:
    def test_wilcoxon(self):
        sample1 = np.array([1, 2, 3, 4, 5])
        sample2 = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        stat, pval = wilcoxon_signed_rank(sample1, sample2)
        assert isinstance(stat, float)
        assert 0 <= pval <= 1

    def test_ttest(self):
        sample1 = np.array([1, 2, 3, 4, 5])
        sample2 = np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        stat, pval = paired_ttest(sample1, sample2)
        assert isinstance(stat, float)
        assert 0 <= pval <= 1

    def test_identical_samples(self):
        """Identical samples should yield p=1.0."""
        sample = np.array([1, 2, 3, 4, 5])
        _, pval = wilcoxon_signed_rank(sample, sample)
        assert pval == 1.0

    def test_shape_mismatch_statistical(self):
        sample1 = np.array([1, 2, 3, 4, 5])
        sample2 = np.array([1, 2, 3])
        with pytest.raises(ValueError):
            wilcoxon_signed_rank(sample1, sample2)

class TestBrierScore:
    def test_perfect_prediction(self):
        y_true = np.array([1, 0, 1, 0])
        y_prob = np.array([1.0, 0.0, 1.0, 0.0])
        score = brier_score(y_true, y_prob)
        assert score == 0.0

    def test_shape_mismatch(self):
        y_true = np.array([1, 0, 1])
        y_prob = np.array([1.0, 0.0])
        with pytest.raises(ValueError):
            brier_score(y_true, y_prob)

    def test_worst_prediction(self):
        """Worst possible prediction should have max Brier score."""
        y_true = np.array([1, 0, 1, 0])
        y_prob = np.array([0.0, 1.0, 0.0, 1.0])
        score = brier_score(y_true, y_prob)
        # Max score for binary is 1.0
        assert score == 1.0

    def test_random_prediction(self):
        """Random prediction should have score around 0.25."""
        np.random.seed(42)
        y_true = np.random.choice([0, 1], size=1000)
        y_prob = np.random.rand(1000)
        score = brier_score(y_true, y_prob)
        # Expected value for random guess on balanced data is 0.25
        assert 0.15 < score < 0.35

class TestEvaluateDetection:
    def test_full_evaluation(self):
        np.random.seed(42)
        y_true = np.random.choice([0, 1], size=200)
        y_pred = np.random.choice([0, 1], size=200)
        y_scores = np.random.rand(200)
        
        results = evaluate_detection(y_true, y_pred, y_scores, bootstrap_n=100, seed=42)
        
        assert 'precision' in results
        assert 'recall' in results
        assert 'f1' in results
        assert 'f1_ci' in results
        assert 'auc_roc' in results
        assert 'auc_roc_ci' in results

    def test_without_scores(self):
        np.random.seed(42)
        y_true = np.random.choice([0, 1], size=100)
        y_pred = np.random.choice([0, 1], size=100)
        
        results = evaluate_detection(y_true, y_pred, y_scores=None, bootstrap_n=50, seed=42)
        
        assert 'precision' in results
        assert 'auc_roc' not in results

    def test_schema_compliance(self):
        """Verify output matches expected schema."""
        np.random.seed(42)
        y_true = np.random.choice([0, 1], size=100)
        y_pred = np.random.choice([0, 1], size=100)
        y_scores = np.random.rand(100)
        
        results = evaluate_detection(y_true, y_pred, y_scores, bootstrap_n=50, seed=42)
        
        # Check required keys
        required_keys = ['precision', 'recall', 'f1', 'f1_ci', 'auc_roc', 'auc_roc_ci']
        for key in required_keys:
            assert key in results, f"Missing key: {key}"
        
        # Check types
        assert isinstance(results['precision'], float)
        assert isinstance(results['recall'], float)
        assert isinstance(results['f1'], float)
        assert isinstance(results['f1_ci'], dict)
        assert 'lower' in results['f1_ci']
        assert 'upper' in results['f1_ci']
        assert isinstance(results['auc_roc'], float)
        assert isinstance(results['auc_roc_ci'], dict)

    def test_edge_case_no_anomalies_in_ground_truth(self):
        """Handle case where ground truth has no anomalies."""
        y_true = np.zeros(100)
        y_pred = np.zeros(100)
        y_scores = np.random.rand(100)
        
        results = evaluate_detection(y_true, y_pred, y_scores, bootstrap_n=50, seed=42)
        
        # Recall should be 0 (or undefined, handled as 0)
        assert results['recall'] == 0.0
        # Precision should be 0 (no positive predictions)
        assert results['precision'] == 0.0
        # F1 should be 0
        assert results['f1'] == 0.0