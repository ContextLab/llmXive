"""
Edge case tests for the embodied curriculum learning pipeline.
Tests cover:
1. Sample size < 30 (insufficient data for sensitivity sweep)
2. Missing required columns in input data
3. High collinearity between predictors
"""

import pytest
import numpy as np
import os
import sys
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import DatasetRecord, AnalysisResult, SensitivitySweep
from src.data_loader import log_skipped_record, calculate_gain_scores, load_public_dataset
from src.stats_engine import run_t_test, calculate_effect_size, check_collinearity
from src.sensitivity import run_sensitivity_sweep, check_robustness_warning
from src.synthetic_gen import SyntheticDataGenerator
from src.logging_config import setup_logging
import logging


class TestEdgeCasesSampleSize:
    """Tests for N < 30 edge cases"""

    def test_sensitivity_sweep_insufficient_data(self):
        """Test that sensitivity sweep returns early with insufficient_data flag when N < 30"""
        # Create small dataset
        small_gain_scores = [1.0, 2.0, 3.0, 4.0, 5.0]  # N=5
        instruction_types = ['embodied', 'embodied', 'static', 'static', 'embodied']
        
        # Create mock AnalysisResult
        analysis_result = AnalysisResult(
            t_statistic=0.0,
            p_value=1.0,
            effect_size=0.0,
            confidence_interval=(0.0, 0.0),
            sample_size=5,
            is_significant=False,
            robustness_warning=False,
            raw_results={}
        )
        
        # Run sensitivity sweep with small dataset
        thresholds = [0.01, 0.05, 0.10]
        sweep_results = run_sensitivity_sweep(
            gain_scores=small_gain_scores,
            instruction_types=instruction_types,
            thresholds=thresholds,
            analysis_result=analysis_result
        )
        
        # Verify early return with insufficient_data flag
        assert len(sweep_results) == 0, "Sweep should return empty list for N < 30"
        assert analysis_result.insufficient_data == True, "Should flag insufficient data"

    def test_t_test_with_very_small_sample(self):
        """Test t-test behavior with N=2 (minimum for variance calculation)"""
        group_a = [1.0, 2.0]  # N=2
        group_b = [3.0, 4.0]  # N=2
        
        # Should not raise exception
        result = run_t_test(group_a, group_b)
        
        assert result['t_statistic'] is not None
        assert result['p_value'] is not None
        assert result['sample_size_a'] == 2
        assert result['sample_size_b'] == 2

    def test_power_calculation_with_small_sample(self):
        """Test power calculation flags underpowered results for small N"""
        from src.stats_engine import calculate_power
        
        # Small sample, small effect
        power = calculate_power(
            effect_size=0.2,
            sample_size_a=10,
            sample_size_b=10,
            alpha=0.05
        )
        
        # Should be underpowered (< 0.80)
        assert power < 0.80, "Small samples should result in underpowered tests"


class TestEdgeCasesMissingColumns:
    """Tests for missing required columns in input data"""

    def test_load_dataset_missing_instruction_type(self):
        """Test that missing instruction_type triggers synthetic generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create CSV with missing instruction_type column
            csv_path = Path(tmpdir) / "missing_cols.csv"
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['pre_test_score', 'post_test_score'])
                writer.writerow([1.0, 2.0])
                writer.writerow([3.0, 4.0])
            
            # Should invoke synthetic generation (which will fail if no real data)
            # For this test, we verify the validation catches the issue
            try:
                # This should fail because instruction_type is required for secondary analysis
                records = load_public_dataset(str(csv_path))
                # If we get here, synthetic generation was invoked
                assert len(records) > 0
            except Exception as e:
                # Expected if synthetic generation fails
                assert "instruction_type" in str(e).lower() or "synthetic" in str(e).lower()

    def test_load_dataset_missing_pre_score(self):
        """Test that missing pre_test_score is logged and skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create CSV with missing pre_test_score
            csv_path = Path(tmpdir) / "missing_pre.csv"
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['post_test_score', 'instruction_type'])
                writer.writerow([2.0, 'embodied'])
                writer.writerow([4.0, 'static'])
            
            # Should skip records with missing pre_test_score
            records = load_public_dataset(str(csv_path))
            
            # All records should be skipped
            assert len(records) == 0

    def test_load_dataset_missing_post_score(self):
        """Test that missing post_test_score is logged and skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create CSV with missing post_test_score
            csv_path = Path(tmpdir) / "missing_post.csv"
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['pre_test_score', 'instruction_type'])
                writer.writerow([1.0, 'embodied'])
                writer.writerow([3.0, 'static'])
            
            # Should skip records with missing post_test_score
            records = load_public_dataset(str(csv_path))
            
            # All records should be skipped
            assert len(records) == 0

    def test_calculate_gain_scores_with_missing_values(self):
        """Test gain score calculation handles missing values correctly"""
        records = [
            DatasetRecord(pre_test_score=1.0, post_test_score=2.0, instruction_type='embodied', covariates={}),
            DatasetRecord(pre_test_score=None, post_test_score=3.0, instruction_type='static', covariates={}),
            DatasetRecord(pre_test_score=2.0, post_test_score=None, instruction_type='embodied', covariates={}),
            DatasetRecord(pre_test_score=3.0, post_test_score=4.0, instruction_type='static', covariates={}),
        ]
        
        gain_scores = calculate_gain_scores(records)
        
        # Should only have 2 valid gain scores
        assert len(gain_scores) == 2
        assert gain_scores[0]['gain_score'] == 1.0  # 2.0 - 1.0
        assert gain_scores[1]['gain_score'] == 1.0  # 4.0 - 3.0

    def test_log_skipped_record_creates_log_file(self):
        """Test that skipped records are logged to file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "skipped_records.log"
            
            log_skipped_record(
                log_path=str(log_path),
                reason="Missing pre_test_score",
                record_id="test_001",
                data={"pre_test_score": None, "post_test_score": 2.0}
            )
            
            # Verify log file was created
            assert log_path.exists()
            
            with open(log_path, 'r') as f:
                content = f.read()
                assert "Missing pre_test_score" in content
                assert "test_001" in content


class TestEdgeCasesCollinearity:
    """Tests for high collinearity between predictors"""

    def test_check_collinearity_high_correlation(self):
        """Test collinearity detection when |r| > 0.8"""
        # Create highly correlated predictors
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = x1 * 0.95 + np.random.normal(0, 0.1, n)  # Highly correlated with x1
        
        predictors = {'x1': x1, 'x2': x2}
        
        collinearity_result = check_collinearity(predictors)
        
        # Should detect high collinearity
        assert collinearity_result['high_collinearity'] == True
        assert collinearity_result['max_correlation'] > 0.8
        assert 'x1' in collinearity_result['correlated_pairs'][0]
        assert 'x2' in collinearity_result['correlated_pairs'][0]

    def test_check_collinearity_low_correlation(self):
        """Test collinearity detection when |r| < 0.8"""
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = np.random.normal(0, 1, n)  # Independent of x1
        
        predictors = {'x1': x1, 'x2': x2}
        
        collinearity_result = check_collinearity(predictors)
        
        # Should not detect high collinearity
        assert collinearity_result['high_collinearity'] == False
        assert collinearity_result['max_correlation'] < 0.8

    def test_check_collinearity_with_multiple_predictors(self):
        """Test collinearity detection with multiple predictors"""
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = np.random.normal(0, 1, n)
        x3 = x1 * 0.9 + np.random.normal(0, 0.1, n)  # Correlated with x1
        
        predictors = {'x1': x1, 'x2': x2, 'x3': x3}
        
        collinearity_result = check_collinearity(predictors)
        
        # Should detect collinearity between x1 and x3
        assert collinearity_result['high_collinearity'] == True
        assert len(collinearity_result['correlated_pairs']) >= 1

    def test_collinearity_with_constant_predictor(self):
        """Test collinearity detection with constant (zero variance) predictor"""
        np.random.seed(42)
        n = 100
        x1 = np.random.normal(0, 1, n)
        x2 = np.ones(n)  # Constant predictor
        
        predictors = {'x1': x1, 'x2': x2}
        
        # Should handle gracefully (constant has undefined correlation)
        collinearity_result = check_collinearity(predictors)
        
        # Should not crash, may report NaN or handle specially
        assert 'high_collinearity' in collinearity_result


class TestEdgeCasesDataValidation:
    """Additional edge case tests for data validation"""

    def test_empty_dataset(self):
        """Test behavior with completely empty dataset"""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "empty.csv"
            with open(csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['pre_test_score', 'post_test_score', 'instruction_type'])
                # No data rows
            
            # Should return empty list
            records = load_public_dataset(str(csv_path))
            assert len(records) == 0

    def test_single_record(self):
        """Test t-test with single record in each group"""
        group_a = [1.0]  # N=1
        group_b = [2.0]  # N=1
        
        # T-test requires at least 2 samples for variance calculation
        # Should handle gracefully
        with pytest.raises(Exception):
            run_t_test(group_a, group_b)

    def test_all_same_values(self):
        """Test t-test when all values in a group are identical"""
        group_a = [1.0, 1.0, 1.0]  # Zero variance
        group_b = [2.0, 2.0, 2.0]  # Zero variance
        
        # Should handle zero variance case
        result = run_t_test(group_a, group_b)
        
        # May return NaN or special value for t-statistic
        assert result['t_statistic'] is not None

    def test_extreme_outliers(self):
        """Test robustness to extreme outliers"""
        np.random.seed(42)
        group_a = np.random.normal(0, 1, 100).tolist()
        group_b = np.random.normal(0, 1, 100).tolist()
        # Add extreme outlier
        group_a.append(1000.0)
        
        # Should not crash
        result = run_t_test(group_a, group_b)
        assert result['t_statistic'] is not None
        assert result['p_value'] is not None

    def test_mixed_instruction_types(self):
        """Test with mixed instruction types in dataset"""
        records = [
            DatasetRecord(pre_test_score=1.0, post_test_score=2.0, instruction_type='embodied', covariates={}),
            DatasetRecord(pre_test_score=2.0, post_test_score=3.0, instruction_type='static', covariates={}),
            DatasetRecord(pre_test_score=3.0, post_test_score=4.0, instruction_type='hybrid', covariates={}),
            DatasetRecord(pre_test_score=4.0, post_test_score=5.0, instruction_type=None, covariates={}),  # Missing
        ]
        
        gain_scores = calculate_gain_scores(records)
        
        # Should skip record with None instruction_type
        assert len(gain_scores) == 3
        assert all(g['instruction_type'] is not None for g in gain_scores)

    def test_negative_gain_scores(self):
        """Test handling of negative gain scores (performance decline)"""
        records = [
            DatasetRecord(pre_test_score=5.0, post_test_score=3.0, instruction_type='embodied', covariates={}),
            DatasetRecord(pre_test_score=4.0, post_test_score=6.0, instruction_type='static', covariates={}),
        ]
        
        gain_scores = calculate_gain_scores(records)
        
        assert len(gain_scores) == 2
        assert gain_scores[0]['gain_score'] == -2.0  # 3.0 - 5.0
        assert gain_scores[1]['gain_score'] == 2.0   # 6.0 - 4.0

    def test_very_large_gain_scores(self):
        """Test handling of very large gain scores"""
        records = [
            DatasetRecord(pre_test_score=0.0, post_test_score=1000.0, instruction_type='embodied', covariates={}),
            DatasetRecord(pre_test_score=0.0, post_test_score=2000.0, instruction_type='static', covariates={}),
        ]
        
        gain_scores = calculate_gain_scores(records)
        
        assert len(gain_scores) == 2
        assert gain_scores[0]['gain_score'] == 1000.0
        assert gain_scores[1]['gain_score'] == 2000.0

    def test_synthetic_generation_with_zero_mean_difference(self):
        """Test synthetic generation with zero mean difference (null hypothesis)"""
        generator = SyntheticDataGenerator(seed=42)
        
        synthetic_data = generator.generate(
            n_samples=100,
            mean_difference=0.0,  # Null hypothesis
            std_dev=1.0,
            instruction_types=['embodied', 'static']
        )
        
        # Should generate data with approximately equal means
        embodied_scores = [r['post_test_score'] - r['pre_test_score'] 
                          for r in synthetic_data if r['instruction_type'] == 'embodied']
        static_scores = [r['post_test_score'] - r['pre_test_score'] 
                        for r in synthetic_data if r['instruction_type'] == 'static']
        
        embodied_mean = np.mean(embodied_scores)
        static_mean = np.mean(static_scores)
        
        # Means should be close (not exactly equal due to randomness)
        assert abs(embodied_mean - static_mean) < 0.5

    def test_synthetic_generation_with_large_mean_difference(self):
        """Test synthetic generation with large mean difference"""
        generator = SyntheticDataGenerator(seed=42)
        
        synthetic_data = generator.generate(
            n_samples=100,
            mean_difference=5.0,  # Large effect
            std_dev=1.0,
            instruction_types=['embodied', 'static']
        )
        
        embodied_scores = [r['post_test_score'] - r['pre_test_score'] 
                          for r in synthetic_data if r['instruction_type'] == 'embodied']
        static_scores = [r['post_test_score'] - r['pre_test_score'] 
                        for r in synthetic_data if r['instruction_type'] == 'static']
        
        embodied_mean = np.mean(embodied_scores)
        static_mean = np.mean(static_scores)
        
        # Embodied should have significantly higher mean
        assert embodied_mean > static_mean
        assert embodied_mean - static_mean > 3.0  # Should be close to 5.0