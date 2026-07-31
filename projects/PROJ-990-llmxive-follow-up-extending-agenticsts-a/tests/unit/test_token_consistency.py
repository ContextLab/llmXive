import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from token_consistency_checker import calculate_token_savings_consistency, load_baseline_comparison, generate_consistency_report

class TestTokenConsistency:
    
    def test_calculate_consistency_passed(self, tmp_path):
        """Test case where std_dev is small relative to mean savings."""
        # Simulate data: Static=4000, Dynamic=3000 (25% reduction), Std=100
        # Mean reduction = (4000-3000)/4000 = 0.25
        # Std reduction = 100/4000 = 0.025
        # Threshold = 0.10 * 0.25 = 0.025
        # 0.025 < 0.025 is False, so we need slightly smaller std or larger mean.
        # Let's try Std=50.
        # Std reduction = 50/4000 = 0.0125. Threshold = 0.025. 0.0125 < 0.025 -> True.
        
        data = {
            'condition': ['static', 'dynamic'],
            'avg_tokens': [4000.0, 3000.0],
            'std_dev_tokens': [0.0, 50.0],
            'token_reduction_pct': [0.0, 0.25]
        }
        df = pd.DataFrame(data)
        
        result = calculate_token_savings_consistency(df)
        
        assert result["passed"] is True
        assert abs(result["mean_reduction_pct"] - 0.25) < 0.001
        assert abs(result["std_reduction_pct"] - 0.0125) < 0.0001

    def test_calculate_consistency_failed(self, tmp_path):
        """Test case where std_dev is large relative to mean savings."""
        # Simulate data: Static=4000, Dynamic=3000 (25% reduction), Std=200
        # Std reduction = 200/4000 = 0.05. Threshold = 0.025.
        # 0.05 < 0.025 -> False.
        
        data = {
            'condition': ['static', 'dynamic'],
            'avg_tokens': [4000.0, 3000.0],
            'std_dev_tokens': [0.0, 200.0],
            'token_reduction_pct': [0.0, 0.25]
        }
        df = pd.DataFrame(data)
        
        result = calculate_token_savings_consistency(df)
        
        assert result["passed"] is False
        
    def test_missing_conditions(self, tmp_path):
        """Test handling of missing static or dynamic rows."""
        data = {
            'condition': ['dynamic'],
            'avg_tokens': [3000.0],
            'std_dev_tokens': [100.0],
            'token_reduction_pct': [0.25]
        }
        df = pd.DataFrame(data)
        
        result = calculate_token_savings_consistency(df)
        assert result["passed"] is False
        assert "Missing" in result["reason"]

    def test_zero_mean_reduction(self, tmp_path):
        """Test handling of zero mean reduction (division by zero)."""
        data = {
            'condition': ['static', 'dynamic'],
            'avg_tokens': [4000.0, 4000.0],
            'std_dev_tokens': [0.0, 100.0],
            'token_reduction_pct': [0.0, 0.0]
        }
        df = pd.DataFrame(data)
        
        result = calculate_token_savings_consistency(df)
        assert result["passed"] is False
        assert "Zero" in result["reason"]