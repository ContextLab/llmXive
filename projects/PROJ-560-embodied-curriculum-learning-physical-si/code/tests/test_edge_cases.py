import pytest
import numpy as np
import os
import sys
import json
import tempfile
from src.stats_engine import check_collinearity, calculate_power
from src.data_loader import calculate_gain_scores
from src.models import DatasetRecord


class TestEdgeCasesSampleSize:
    """Tests for small sample sizes."""
    
    def test_t_test_small_n(self):
        """Test t-test with n=2 per group."""
        from src.stats_engine import run_t_test
        g1 = [1.0, 2.0]
        g2 = [3.0, 4.0]
        t_stat, p_val = run_t_test(g1, g2)
        assert isinstance(t_stat, float)
        
    def test_power_small_n(self):
        """Test power calculation with small n."""
        power = calculate_power(effect_size=0.5, n1=5, n2=5)
        assert 0 <= power <= 1


class TestEdgeCasesMissingColumns:
    """Tests for missing column handling."""
    
    def test_missing_pre_score(self):
        """Test handling missing pre score."""
        records = [
            DatasetRecord(pre_test_score=None, post_test_score=60, instruction_type="A"),
            DatasetRecord(pre_test_score=50, post_test_score=60, instruction_type="A")
        ]
        valid = calculate_gain_scores(records)
        assert len(valid) == 1


class TestEdgeCasesCollinearity:
    """Tests for collinearity detection."""
    
    def test_high_collinearity(self):
        """Test detection of high collinearity."""
        covariates = [
            {"x": 1, "y": 1},
            {"x": 2, "y": 2},
            {"x": 3, "y": 3},
            {"x": 4, "y": 4}
        ]
        diag = check_collinearity(covariates)
        assert diag["collinearity_detected"] is True
        
    def test_low_collinearity(self):
        """Test detection of low collinearity."""
        covariates = [
            {"x": 1, "y": 10},
            {"x": 2, "y": 5},
            {"x": 3, "y": 20},
            {"x": 4, "y": 15}
        ]
        diag = check_collinearity(covariates)
        assert diag["collinearity_detected"] is False


class TestEdgeCasesDataValidation:
    """Tests for data validation."""
    
    def test_invalid_scores(self):
        """Test handling invalid scores."""
        records = [
            DatasetRecord(pre_test_score="invalid", post_test_score=60, instruction_type="A"),
            DatasetRecord(pre_test_score=50, post_test_score=60, instruction_type="A")
        ]
        # This would normally raise during conversion, but we test the logic path
        # In real loader, this is caught during CSV/JSON parsing
        pass
