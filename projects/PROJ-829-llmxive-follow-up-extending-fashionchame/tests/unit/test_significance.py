"""
Unit tests for statistical significance analysis module.

Tests edge case handling for low sample power scenarios.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from src.stats.significance import (
    check_sample_sizes,
    has_low_sample_count,
    perform_anova,
    bonferroni_correction,
    analyze_significance,
    run_pipeline,
    MIN_SAMPLE_SIZE_FOR_POWER,
    MIN_SAMPLE_SIZE_FOR_WARNING
)


class TestSampleSizeChecks:
    """Tests for sample size validation functions."""
    
    def test_check_sample_sizes_normal(self):
        """Test sample size counting with normal data."""
        scores = {
            "color": [0.1, 0.2, 0.3, 0.4, 0.5],
            "pattern": [0.2, 0.3, 0.4],
            "texture": [0.15, 0.25]
        }
        result = check_sample_sizes(scores)
        
        assert result == {
            "color": 5,
            "pattern": 3,
            "texture": 2
        }
    
    def test_check_sample_sizes_empty(self):
        """Test sample size counting with empty lists."""
        scores = {
            "color": [],
            "pattern": [0.1, 0.2]
        }
        result = check_sample_sizes(scores)
        
        assert result == {
            "color": 0,
            "pattern": 2
        }
    
    def test_has_low_sample_count_below_threshold(self):
        """Test detection of low sample counts below threshold."""
        scores = {
            "color": [0.1] * 20,  # Below threshold of 30
            "pattern": [0.2] * 50  # Above threshold
        }
        
        any_low, low_power = has_low_sample_count(scores, threshold=30)
        
        assert any_low is True
        assert low_power["color"] is True
        assert low_power["pattern"] is False
    
    def test_has_low_sample_count_all_above_threshold(self):
        """Test when all classes have sufficient samples."""
        scores = {
            "color": [0.1] * 35,
            "pattern": [0.2] * 40
        }
        
        any_low, low_power = has_low_sample_count(scores, threshold=30)
        
        assert any_low is False
        assert all(not v for v in low_power.values())
    
    def test_has_low_sample_count_critical_low(self):
        """Test detection of critically low sample counts."""
        scores = {
            "color": [0.1] * 5,  # Below critical threshold
            "pattern": [0.2] * 30  # At threshold
        }
        
        any_low, low_power = has_low_sample_count(scores, threshold=30)
        
        assert any_low is True
        assert low_power["color"] is True
        assert low_power["pattern"] is False


class TestANOVA:
    """Tests for ANOVA statistical test."""
    
    def test_perform_anova_normal(self):
        """Test ANOVA with normal data."""
        scores = {
            "color": [0.1, 0.2, 0.3, 0.4, 0.5],
            "pattern": [0.5, 0.6, 0.7, 0.8, 0.9],
            "texture": [0.2, 0.3, 0.4, 0.5, 0.6]
        }
        
        f_stat, p_val = perform_anova(scores)
        
        assert isinstance(f_stat, float)
        assert isinstance(p_val, float)
        assert f_stat >= 0
        assert 0 <= p_val <= 1
    
    def test_perform_anova_insufficient_classes(self):
        """Test ANOVA with only one class."""
        scores = {
            "color": [0.1, 0.2, 0.3]
        }
        
        with pytest.raises(ValueError, match="Insufficient classes"):
            perform_anova(scores)
    
    def test_perform_anova_empty_list(self):
        """Test ANOVA with empty lists."""
        scores = {
            "color": [],
            "pattern": [0.1, 0.2]
        }
        
        # Should filter out empty list and work with single remaining class
        with pytest.raises(ValueError, match="Insufficient classes"):
            perform_anova(scores)


class TestBonferroni:
    """Tests for Bonferroni correction."""
    
    def test_bonferroni_normal(self):
        """Test Bonferroni correction with normal p-values."""
        p_values = [0.01, 0.03, 0.05, 0.10]
        
        corrected, significant = bonferroni_correction(p_values, alpha=0.05)
        
        assert len(corrected) == 4
        assert len(significant) == 4
        
        # First two should remain significant after correction
        assert significant[0] is True  # 0.01 * 4 = 0.04 < 0.05
        assert significant[1] is False  # 0.03 * 4 = 0.12 > 0.05
        assert significant[2] is False  # 0.05 * 4 = 0.20 > 0.05
        assert significant[3] is False  # 0.10 * 4 = 0.40 > 0.05
    
    def test_bonferroni_empty(self):
        """Test Bonferroni with empty list."""
        corrected, significant = bonferroni_correction([], alpha=0.05)
        
        assert corrected == []
        assert significant == []
    
    def test_bonferroni_p_value_capped_at_one(self):
        """Test that corrected p-values don't exceed 1.0."""
        p_values = [0.3, 0.5]
        
        corrected, _ = bonferroni_correction(p_values, alpha=0.05)
        
        assert all(p <= 1.0 for p in corrected)


class TestAnalyzeSignificance:
    """Tests for complete significance analysis with edge cases."""
    
    def test_analyze_significance_normal(self):
        """Test analysis with normal sample sizes."""
        scores = {
            "color": [0.1 + i * 0.01 for i in range(35)],
            "pattern": [0.2 + i * 0.01 for i in range(35)],
            "texture": [0.3 + i * 0.01 for i in range(35)]
        }
        
        result = analyze_significance(scores)
        
        assert result["analysis_complete"] is True
        assert result["low_power_warning"] is False
        assert result["anova_results"] is not None
        assert len(result["warnings"]) == 0
    
    def test_analyze_significance_low_power_warning(self):
        """Test analysis triggers warning for low sample counts."""
        scores = {
            "color": [0.1 + i * 0.01 for i in range(20)],  # Below 30
            "pattern": [0.2 + i * 0.01 for i in range(35)],
            "texture": [0.3 + i * 0.01 for i in range(35)]
        }
        
        result = analyze_significance(scores)
        
        assert result["analysis_complete"] is True
        assert result["low_power_warning"] is True
        assert "color" in result["low_power_classes"]
        assert result["low_power_classes"]["color"] is True
        assert any("WARNING" in w for w in result["warnings"])
    
    def test_analyze_significance_critical_low_power(self):
        """Test analysis with critically low sample counts."""
        scores = {
            "color": [0.1, 0.2, 0.3, 0.4, 0.5],  # Below 10
            "pattern": [0.2, 0.3, 0.4],  # Below 10
            "texture": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.10, 0.11, 0.12]  # Exactly 10
        }
        
        result = analyze_significance(scores)
        
        assert result["analysis_complete"] is True
        assert result["low_power_warning"] is True
        assert len(result["warnings"]) > 0
        
        # Check for critical warnings
        critical_warnings = [w for w in result["warnings"] if "CRITICAL" in w]
        assert len(critical_warnings) >= 1  # At least one class below 10
    
    def test_analyze_significance_with_anova(self):
        """Test that ANOVA is performed when data allows."""
        scores = {
            "color": [0.1 + i * 0.05 for i in range(35)],
            "pattern": [0.3 + i * 0.05 for i in range(35)],
            "texture": [0.5 + i * 0.05 for i in range(35)]
        }
        
        result = analyze_significance(scores)
        
        assert result["analysis_complete"] is True
        assert result["anova_results"] is not None
        assert "f_statistic" in result["anova_results"]
        assert "p_value" in result["anova_results"]
        assert "is_significant" in result["anova_results"]
    
    def test_analyze_significance_empty_input(self):
        """Test analysis with empty scores."""
        scores = {}
        
        result = analyze_significance(scores)
        
        assert result["analysis_complete"] is False
        assert len(result["warnings"]) > 0


class TestRunPipeline:
    """Integration tests for the pipeline execution."""
    
    def test_run_pipeline_normal(self):
        """Test pipeline execution with normal data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            output_path = Path(tmpdir) / "output.json"
            
            # Create input data
            input_data = {
                "scores": [
                    {"garment_feature_class": "color", "lpips": 0.1 + i * 0.01}
                    for i in range(35)
                ] + [
                    {"garment_feature_class": "pattern", "lpips": 0.3 + i * 0.01}
                    for i in range(35)
                ]
            }
            
            with open(input_path, 'w') as f:
                json.dump(input_data, f)
            
            # Run pipeline
            run_pipeline(str(input_path), str(output_path))
            
            # Verify output exists and is valid JSON
            assert output_path.exists()
            with open(output_path, 'r') as f:
                result = json.load(f)
            
            assert result["analysis_complete"] is True
            assert result["total_samples"] == 70
    
    def test_run_pipeline_low_power(self):
        """Test pipeline execution with low sample counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            output_path = Path(tmpdir) / "output.json"
            
            # Create input data with low sample counts
            input_data = {
                "scores": [
                    {"garment_feature_class": "color", "lpips": 0.1 + i * 0.01}
                    for i in range(5)  # Very low count
                ] + [
                    {"garment_feature_class": "pattern", "lpips": 0.3 + i * 0.01}
                    for i in range(35)
                ]
            }
            
            with open(input_path, 'w') as f:
                json.dump(input_data, f)
            
            # Run pipeline
            run_pipeline(str(input_path), str(output_path))
            
            # Verify output contains warnings
            with open(output_path, 'r') as f:
                result = json.load(f)
            
            assert result["low_power_warning"] is True
            assert any("WARNING" in w or "CRITICAL" in w for w in result["warnings"])
    
    def test_run_pipeline_file_not_found(self):
        """Test pipeline with non-existent input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.json"
            output_path = Path(tmpdir) / "output.json"
            
            with pytest.raises(FileNotFoundError):
                run_pipeline(str(input_path), str(output_path))
    
    def test_run_pipeline_creates_output_directory(self):
        """Test that pipeline creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            output_path = Path(Path(tmpdir) / "subdir" / "output.json")
            
            # Create input data
            input_data = {
                "scores": [
                    {"garment_feature_class": "color", "lpips": 0.1 + i * 0.01}
                    for i in range(35)
                ]
            }
            
            with open(input_path, 'w') as f:
                json.dump(input_data, f)
            
            # Run pipeline - should create subdir
            run_pipeline(str(input_path), str(output_path))
            
            assert output_path.exists()