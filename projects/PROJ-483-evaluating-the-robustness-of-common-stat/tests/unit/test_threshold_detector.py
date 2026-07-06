import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
code_path = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from threshold_detector import find_threshold_exceedance

class TestThresholdDetector:
    def test_basic_exceedance_detection(self):
        """Test that the function correctly identifies the first r where error > 0.10"""
        data = {
            "test_type": ["t-test", "t-test", "t-test", "t-test"],
            "dependency_structure": ["ar1", "ar1", "ar1", "ar1"],
            "dependency_strength": [0.0, 0.1, 0.2, 0.3],
            "observed_type1_error": [0.05, 0.08, 0.12, 0.15]
        }
        df = pd.DataFrame(data)
        
        result = find_threshold_exceedance(df, alpha_threshold=0.10)
        
        assert len(result) == 1
        assert result.iloc[0]["status"] == "exceeded"
        assert result.iloc[0]["threshold_r"] == 0.2
        assert result.iloc[0]["error_rate_at_threshold"] == 0.12

    def test_no_exceedance(self):
        """Test handling when error rate never exceeds threshold"""
        data = {
            "test_type": ["anova", "anova", "anova"],
            "dependency_structure": ["block", "block", "block"],
            "dependency_strength": [0.0, 0.3, 0.6],
            "observed_type1_error": [0.05, 0.06, 0.07]
        }
        df = pd.DataFrame(data)
        
        result = find_threshold_exceedance(df, alpha_threshold=0.10)
        
        assert len(result) == 1
        assert result.iloc[0]["status"] == "never_exceeded"
        assert pd.isna(result.iloc[0]["threshold_r"])
        assert result.iloc[0]["error_rate_at_threshold"] == 0.07

    def test_multiple_test_types(self):
        """Test detection across multiple test types and structures"""
        data = {
            "test_type": ["t-test", "t-test", "chi2", "chi2"],
            "dependency_structure": ["ar1", "ar1", "spatial", "spatial"],
            "dependency_strength": [0.0, 0.5, 0.0, 0.5],
            "observed_type1_error": [0.05, 0.15, 0.05, 0.09]
        }
        df = pd.DataFrame(data)
        
        result = find_threshold_exceedance(df, alpha_threshold=0.10)
        
        assert len(result) == 2
        
        # Check t-test result
        ttest_row = result[result["test_type"] == "t-test"].iloc[0]
        assert ttest_row["status"] == "exceeded"
        assert ttest_row["threshold_r"] == 0.5
        
        # Check chi2 result
        chi2_row = result[result["test_type"] == "chi2"].iloc[0]
        assert chi2_row["status"] == "never_exceeded"

    def test_empty_dataframe(self):
        """Test handling of empty input"""
        df = pd.DataFrame(columns=["test_type", "dependency_structure", "dependency_strength", "observed_type1_error"])
        result = find_threshold_exceedance(df)
        assert len(result) == 0

    def test_unsorted_input(self):
        """Test that function handles unsorted dependency strength correctly"""
        data = {
            "test_type": ["t-test", "t-test", "t-test"],
            "dependency_structure": ["ar1", "ar1", "ar1"],
            "dependency_strength": [0.3, 0.0, 0.2], # Unsorted
            "observed_type1_error": [0.15, 0.05, 0.12]
        }
        df = pd.DataFrame(data)
        
        result = find_threshold_exceedance(df, alpha_threshold=0.10)
        
        # Should still find 0.2 as the first exceedance after sorting
        assert result.iloc[0]["threshold_r"] == 0.2