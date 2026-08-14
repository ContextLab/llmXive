import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from analysis.centrality import run_centrality_analysis, calculate_vif
from utils.config import get_output_paths

def test_vif_below_threshold_uses_global_centrality():
    """Test that when VIF is low, Global_Centrality is used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        # Create synthetic data with low correlation between features
        np.random.seed(42)
        n = 50
        data = {
            "Subject": [f"sub-{i:03d}" for i in range(n)],
            "degree_node_1": np.random.rand(n),
            "degree_node_2": np.random.rand(n),
            "degree_node_3": np.random.rand(n),
            "betweenness_node_1": np.random.rand(n),
            "betweenness_node_2": np.random.rand(n),
            "eigenvector_node_1": np.random.rand(n),
            "Age": np.random.randint(18, 65, n),
            "Sex": np.random.choice(["M", "F"], n),
            "Mean_FD": np.random.rand(n) * 0.2
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        result = run_centrality_analysis(input_path, output_path, vif_threshold=5.0)
        
        assert "Global_Centrality" in result.columns
        assert "PCA_Centrality" not in result.columns
        assert "Age" in result.columns
        assert "Sex" in result.columns
        assert "Mean_FD" in result.columns

def test_vif_above_threshold_uses_pca():
    """Test that when VIF is high, PCA component is used."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        # Create synthetic data with high correlation (collinearity)
        np.random.seed(42)
        n = 50
        base = np.random.rand(n)
        data = {
            "Subject": [f"sub-{i:03d}" for i in range(n)],
            "degree_node_1": base,
            "degree_node_2": base * 0.95 + np.random.rand(n) * 0.01,
            "degree_node_3": base * 0.98 + np.random.rand(n) * 0.01,
            "betweenness_node_1": base * 0.97 + np.random.rand(n) * 0.01,
            "betweenness_node_2": base * 0.96 + np.random.rand(n) * 0.01,
            "eigenvector_node_1": base * 0.99 + np.random.rand(n) * 0.01,
            "Age": np.random.randint(18, 65, n),
            "Sex": np.random.choice(["M", "F"], n),
            "Mean_FD": np.random.rand(n) * 0.2
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        result = run_centrality_analysis(input_path, output_path, vif_threshold=5.0)
        
        assert "PCA_Centrality" in result.columns
        assert "Global_Centrality" not in result.columns
        assert "Age" in result.columns
        assert "Sex" in result.columns
        assert "Mean_FD" in result.columns

def test_vif_calculation():
    """Test VIF calculation function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        
        # Create data with known collinearity
        np.random.seed(42)
        n = 50
        base = np.random.rand(n)
        data = {
            "feature1": base,
            "feature2": base * 0.99,
            "feature3": np.random.rand(n)
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        vif_results = calculate_vif(df, ["feature1", "feature2", "feature3"])
        
        # feature1 and feature2 should have high VIF
        assert vif_results["feature1"] > 10
        assert vif_results["feature2"] > 10
        # feature3 should have low VIF
        assert vif_results["feature3"] < 2
