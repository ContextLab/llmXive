import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis import calculate_vif, apply_pca, run_vif_check_and_pca
from code.config import get_path, ensure_dirs

class TestVIF:
    @pytest.fixture
    def low_corr_data(self):
        """Data with low correlation between predictors."""
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            'A': np.random.normal(0, 1, n),
            'B': np.random.normal(0, 1, n),
            'C': np.random.normal(0, 1, n)
        })

    @pytest.fixture
    def high_corr_data(self):
        """Data with high correlation (multicollinearity)."""
        np.random.seed(42)
        n = 100
        base = np.random.normal(0, 1, n)
        return pd.DataFrame({
            'A': base,
            'B': base * 0.95 + np.random.normal(0, 0.1, n), # High correlation
            'C': np.random.normal(0, 1, n)
        })

    def test_vif_low_correlation(self, low_corr_data):
        """VIF should be low (~1) for uncorrelated predictors."""
        vif_scores = calculate_vif(low_corr_data, ['A', 'B', 'C'])
        for score in vif_scores.values():
            assert score < 5.0, f"VIF {score} is unexpectedly high for uncorrelated data."

    def test_vif_high_correlation(self, high_corr_data):
        """VIF should be high (>5) for highly correlated predictors."""
        vif_scores = calculate_vif(high_corr_data, ['A', 'B', 'C'])
        # A and B are correlated
        assert vif_scores['A'] > 5.0 or vif_scores['B'] > 5.0, \
            "Expected at least one VIF > 5.0 for correlated data."

    def test_run_vif_check_and_pca_creates_artifact(self, high_corr_data, tmp_path):
        """Verify that run_vif_check_and_pca writes the JSON artifact and triggers PCA."""
        output_path = str(tmp_path / "vif_check.json")
        
        result = run_vif_check_and_pca(
            high_corr_data, 
            ['A', 'B', 'C'], 
            vif_threshold=5.0,
            output_path=output_path
        )
        
        # Check artifact exists
        assert Path(output_path).exists(), "VIF check JSON artifact was not created."
        
        # Check content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert "vif_scores" in data
        assert "trigger_pca" in data
        assert data["trigger_pca"] is True, "Expected trigger_pca to be True for high VIF."
        
        # Check result structure
        assert "data" in result
        # If PCA triggered, data should have PC columns
        assert "PC1" in result["data"].columns

    def test_run_vif_check_and_pca_no_pca(self, low_corr_data, tmp_path):
        """Verify no PCA is triggered when VIF is low."""
        output_path = str(tmp_path / "vif_check.json")
        
        result = run_vif_check_and_pca(
            low_corr_data, 
            ['A', 'B', 'C'], 
            vif_threshold=5.0,
            output_path=output_path
        )
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["trigger_pca"] is False
        # Data should be original columns
        assert "PC1" not in result["data"].columns
        assert "A" in result["data"].columns