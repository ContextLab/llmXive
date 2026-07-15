"""
Unit tests for Bayesian statistical analysis in statistical_analysis.py.
"""
import pytest
import os
import tempfile
import pandas as pd
from unittest.mock import patch, MagicMock

def test_load_results_data():
    """Test loading results.csv for analysis."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_path = os.path.join(tmpdir, "results.csv")
        test_data = {
            "prompt": ["p1", "p2"],
            "effect": ["e1", "e2"],
            "quantization": ["fp16", "int8"],
            "similarity": [0.9, 0.8],
            "lpips": [0.1, 0.2]
        }
        df = pd.DataFrame(test_data)
        df.to_csv(results_path, index=False)
        
        from statistical_analysis import load_results_data
        result = load_results_data(results_path)
        assert len(result) == 2
        assert "similarity" in result.columns

def test_prepare_bhm_data():
    """Test data preparation for Bayesian Hierarchical Model."""
    df = pd.DataFrame({
        "prompt": ["p1", "p2", "p1", "p2"],
        "effect": ["e1", "e1", "e2", "e2"],
        "quantization": ["fp16", "fp16", "int8", "int8"],
        "similarity": [0.9, 0.85, 0.8, 0.75]
    })
    
    with patch.dict("sys.modules", {
        "pymc": MagicMock(),
        "bambi": MagicMock()
    }):
        from statistical_analysis import prepare_bhm_data
        result = prepare_bhm_data(df)
        assert result is not None

def test_run_bayesian_model():
    """Test running Bayesian Hierarchical Model."""
    with patch.dict("sys.modules", {
        "pymc": MagicMock(),
        "arviz": MagicMock()
    }):
        from statistical_analysis import run_bayesian_model
        
        # Mock the model and inference
        mock_model = MagicMock()
        mock_idata = MagicMock()
        
        with patch('pymc.Model', return_value=mock_model):
            with patch('pymc.sample', return_value=mock_idata):
                result = run_bayesian_model("similarity ~ quantization + (1|prompt)")
                assert result == mock_idata

def test_compute_correlation():
    """Test correlation computation between subspace rank and concept bleeding."""
    import numpy as np
    subspace_ranks = [5, 3, 8, 2, 6]
    bleeding_magnitudes = [0.1, 0.3, 0.05, 0.4, 0.15]
    
    with patch.dict("sys.modules", {
        "scipy": MagicMock()
    }):
        from statistical_analysis import compute_correlation
        
        # Mock scipy.stats.pearsonr
        mock_result = MagicMock()
        mock_result.statistic = -0.8
        mock_result.pvalue = 0.05
        
        with patch('scipy.stats.pearsonr', return_value=mock_result):
            corr, pval = compute_correlation(subspace_ranks, bleeding_magnitudes)
            assert corr == -0.8
            assert pval == 0.05

def test_posterior_width_analysis():
    """Test posterior width analysis for underpowered results."""
    import numpy as np
    with patch.dict("sys.modules", {
        "arviz": MagicMock()
    }):
        from statistical_analysis import posterior_width_analysis
        
        # Mock idata with wide credible intervals
        mock_summary = MagicMock()
        mock_summary.hdi.return_value = {
            "quantization": [0.0, 0.5]  # Width = 0.5 > 0.2
        }
        
        with patch('arviz.summary', return_value=mock_summary):
            result = posterior_width_analysis("mock_idata")
            assert result["underpowered"] is True
            assert result["credible_interval_width"] == 0.5

def test_flag_underpowered():
    """Test flagging underpowered results."""
    from statistical_analysis import flag_underpowered
    
    # Test with wide CI
    assert flag_underpowered(0.25) is True
    assert flag_underpowered(0.15) is False
    assert flag_underpowered(0.20) is False  # Exactly 0.2 is not underpowered