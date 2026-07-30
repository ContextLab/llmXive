import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.evaluation import (
    generate_stratified_random_baseline,
    compute_f1_scores,
    wilcoxon_signed_rank_test
)

class TestGenerateStratifiedRandomBaseline:
    def test_stratified_sampling_by_rubric_type(self):
        """Test that baseline is stratified by rubric type"""
        # Create sample data with different rubric types
        data = pd.DataFrame({
            'rubric_type': ['Lexical', 'Lexical', 'Format', 'Format', 'Tone', 'Tone'],
            'hacked_label': [1, 0, 1, 1, 0, 1],
            'seed_id': [1, 1, 1, 1, 1, 1]
        })
        
        # Generate baseline with 100% sampling
        baseline_df = generate_stratified_random_baseline(data, 1.0, seed=42)
        
        # All samples should be selected
        assert baseline_df['baseline_label'].sum() == len(data)
        
    def test_fractional_sampling(self):
        """Test that fractional sampling works correctly"""
        data = pd.DataFrame({
            'rubric_type': ['Lexical'] * 10 + ['Format'] * 10,
            'hacked_label': [1] * 10 + [0] * 10,
            'seed_id': [1] * 20
        })
        
        # Generate baseline with 50% sampling
        baseline_df = generate_stratified_random_baseline(data, 0.5, seed=42)
        
        # Approximately half should be selected
        selected = baseline_df['baseline_label'].sum()
        assert 8 <= selected <= 12  # Allow some variance due to randomness
        
    def test_reproducibility_with_seed(self):
        """Test that same seed produces same results"""
        data = pd.DataFrame({
            'rubric_type': ['Lexical'] * 5 + ['Format'] * 5,
            'hacked_label': [1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
            'seed_id': [1] * 10
        })
        
        baseline1 = generate_stratified_random_baseline(data, 0.5, seed=42)
        baseline2 = generate_stratified_random_baseline(data, 0.5, seed=42)
        
        # Results should be identical
        pd.testing.assert_frame_equal(baseline1, baseline2)

class TestComputeF1Scores:
    def test_perfect_prediction(self):
        """Test F1 score for perfect prediction"""
        predicted = pd.Series([1, 0, 1, 0, 1])
        ground_truth = pd.Series([1, 0, 1, 0, 1])
        
        f1 = compute_f1_scores(predicted, ground_truth)
        assert f1 == 1.0
        
    def test_no_true_positives(self):
        """Test F1 score when there are no true positives"""
        predicted = pd.Series([0, 0, 0, 0, 0])
        ground_truth = pd.Series([1, 1, 1, 1, 1])
        
        f1 = compute_f1_scores(predicted, ground_truth)
        assert f1 == 0.0
        
    def test_all_predicted_positive(self):
        """Test F1 score when all predicted positive"""
        predicted = pd.Series([1, 1, 1, 1, 1])
        ground_truth = pd.Series([1, 1, 0, 0, 0])
        
        f1 = compute_f1_scores(predicted, ground_truth)
        # Precision = 2/5, Recall = 2/2 = 1
        # F1 = 2 * (0.4 * 1) / (0.4 + 1) = 0.8 / 1.4 ≈ 0.571
        assert abs(f1 - 0.57142857) < 1e-6
        
    def test_empty_series(self):
        """Test F1 score with empty series"""
        predicted = pd.Series([], dtype=int)
        ground_truth = pd.Series([], dtype=int)
        
        f1 = compute_f1_scores(predicted, ground_truth)
        assert f1 == 0.0

class TestWilcoxonSignedRankTest:
    def test_identical_scores(self):
        """Test Wilcoxon test with identical scores"""
        detector_scores = [0.5, 0.6, 0.7]
        baseline_scores = [0.5, 0.6, 0.7]
        
        p_value, effect_size = wilcoxon_signed_rank_test(detector_scores, baseline_scores)
        
        # p-value should be 1.0 for identical scores
        assert p_value == 1.0
        assert effect_size == 0.0
        
    def test_significant_difference(self):
        """Test Wilcoxon test with significant difference"""
        detector_scores = [0.8, 0.9, 0.85, 0.9, 0.88]
        baseline_scores = [0.5, 0.5, 0.5, 0.5, 0.5]
        
        p_value, effect_size = wilcoxon_signed_rank_test(detector_scores, baseline_scores)
        
        # p-value should be small (significant difference)
        assert p_value < 0.05
        assert effect_size > 0.5  # Large effect size
        
    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise an error"""
        detector_scores = [0.5, 0.6, 0.7]
        baseline_scores = [0.5, 0.6]
        
        with pytest.raises(ValueError, match="must have the same length"):
            wilcoxon_signed_rank_test(detector_scores, baseline_scores)
            
    def test_empty_scores(self):
        """Test that empty scores raise an error"""
        detector_scores = []
        baseline_scores = []
        
        with pytest.raises(ValueError, match="cannot be empty"):
            wilcoxon_signed_rank_test(detector_scores, baseline_scores)
            
    def test_effect_size_calculation(self):
        """Test effect size calculation"""
        # Create scores with known effect
        np.random.seed(42)
        detector_scores = np.random.normal(0.8, 0.1, 20)
        baseline_scores = np.random.normal(0.5, 0.1, 20)
        
        p_value, effect_size = wilcoxon_signed_rank_test(
            detector_scores.tolist(), 
            baseline_scores.tolist()
        )
        
        # Effect size should be positive
        assert effect_size > 0
        # Effect size should be reasonable (between 0 and 1 typically)
        assert 0 <= effect_size <= 1.5