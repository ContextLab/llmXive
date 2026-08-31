import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from eval.stats import (
    load_scores_csv, load_mask_metrics_csv,
    merge_scores_and_metrics, calculate_pearson_correlation,
    run_correlation_analysis
)

class TestStats:
    def test_calculate_pearson_correlation_perfect(self):
        """Test Pearson correlation with perfect positive correlation"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        r, p = calculate_pearson_correlation(x, y)
        
        assert r > 0.99
        assert p < 0.05

    def test_calculate_pearson_correlation_negative(self):
        """Test Pearson correlation with perfect negative correlation"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 4, 3, 2, 1])
        
        r, p = calculate_pearson_correlation(x, y)
        
        assert r < -0.99
        assert p < 0.05

    def test_calculate_pearson_correlation_none(self):
        """Test Pearson correlation with no correlation"""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        
        r, p = calculate_pearson_correlation(x, y)
        
        # Should be close to 0
        assert abs(r) < 0.3

    def test_calculate_pearson_correlation_constant(self):
        """Test Pearson correlation with constant values"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 1, 1, 1, 1])
        
        r, p = calculate_pearson_correlation(x, y)
        
        # Should be NaN or 0
        assert np.isnan(r) or r == 0.0

    def test_merge_scores_and_metrics(self):
        """Test merging of scores and metrics"""
        scores = [
            {'image_id': 'img1', 'score': 3.5},
            {'image_id': 'img2', 'score': 4.2}
        ]
        
        metrics = [
            {'image_id': 'img1', 'gradient_variance': 0.1},
            {'image_id': 'img2', 'gradient_variance': 0.2}
        ]
        
        merged = merge_scores_and_metrics(scores, metrics)
        
        assert len(merged) == 2
        assert 'score' in merged[0]
        assert 'gradient_variance' in merged[0]
        assert merged[0]['image_id'] == 'img1'

    def test_run_correlation_analysis(self):
        """Test full correlation analysis pipeline"""
        import tempfile
        import csv
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create scores file
            scores_path = f"{tmpdir}/scores.csv"
            with open(scores_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['image_id', 'score'])
                for i in range(10):
                    writer.writerow([f'img{i}', i * 1.0])
            
            # Create metrics file
            metrics_path = f"{tmpdir}/metrics.csv"
            with open(metrics_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['image_id', 'gradient_variance', 'texture_entropy'])
                for i in range(10):
                    writer.writerow([f'img{i}', i * 0.5, i * 0.3])
            
            result = run_correlation_analysis(
                scores_path, 
                metrics_path,
                'gradient_variance'
            )
            
            assert 'pearson_r' in result
            assert 'p_value' in result
            assert result['pearson_r'] > 0.9
            assert result['p_value'] < 0.05

    def test_load_scores_csv(self):
        """Test loading scores from CSV"""
        import tempfile
        import csv
        
        with tempfile.TemporaryDirectory() as tmpdir:
            scores_path = f"{tmpdir}/scores.csv"
            with open(scores_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['image_id', 'score'])
                writer.writerow(['img1', 3.5])
                writer.writerow(['img2', 4.2])
            
            scores = load_scores_csv(scores_path)
            
            assert len(scores) == 2
            assert scores[0]['image_id'] == 'img1'
            assert scores[0]['score'] == 3.5

    def test_load_mask_metrics_csv(self):
        """Test loading metrics from CSV"""
        import tempfile
        import csv
        
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = f"{tmpdir}/metrics.csv"
            with open(metrics_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['image_id', 'gradient_variance'])
                writer.writerow(['img1', 0.15])
                writer.writerow(['img2', 0.25])
            
            metrics = load_mask_metrics_csv(metrics_path)
            
            assert len(metrics) == 2
            assert metrics[0]['image_id'] == 'img1'
            assert metrics[0]['gradient_variance'] == 0.15
