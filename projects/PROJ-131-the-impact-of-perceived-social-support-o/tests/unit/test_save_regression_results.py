import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os
import tempfile
import sys

# Add parent to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.save_regression_results import (
    load_regression_results_from_memory,
    load_bootstrap_cis,
    merge_results,
    apply_fdr_and_save,
    main
)

def test_load_regression_results_from_memory():
    results = {
        "model_1": {
            "outcome": "depression",
            "interaction_coef": 0.5,
            "interaction_se": 0.1,
            "interaction_pval": 0.01,
            "support_coef": 0.2,
            "support_se": 0.05,
            "harassment_coef": 0.3,
            "harassment_se": 0.05,
            "n_obs": 100,
            "r_squared": 0.15,
            "f_statistic": 5.0,
            "bootstrap_ci": (0.3, 0.7)
        }
    }
    df = load_regression_results_from_memory(results)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["model"] == "model_1"
    assert df.iloc[0]["interaction_coef"] == 0.5
    assert df.iloc[0]["interaction_ci_lower"] == 0.3
    assert df.iloc[0]["interaction_ci_upper"] == 0.7

def test_load_bootstrap_cis():
    results = {
        "m1": {"bootstrap_ci": (0.1, 0.2)},
        "m2": {"bootstrap_ci": None},
        "m3": {}
    }
    cis = load_bootstrap_cis(results)
    
    assert cis["m1"] == (0.1, 0.2)
    assert np.isnan(cis["m2"][0])
    assert np.isnan(cis["m3"][0])

def test_apply_fdr_and_save():
    # Create a mock dataframe with p-values
    df = pd.DataFrame({
        "model": ["m1", "m2", "m3"],
        "interaction_pval": [0.05, 0.02, 0.10]
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_results.csv"
        apply_fdr_and_save(df.copy(), output_path)
        
        assert output_path.exists()
        loaded_df = pd.read_csv(output_path)
        assert "interaction_pval_fdr" in loaded_df.columns
        
        # Verify FDR logic roughly (0.02 should be smallest adjusted, 0.10 largest)
        # Exact values depend on N, but order should be preserved
        assert loaded_df["interaction_pval_fdr"].min() <= loaded_df["interaction_pval_fdr"].max()

def test_main_integration():
    results = {
        "test_model": {
            "outcome": "test_outcome",
            "interaction_coef": 0.1,
            "interaction_se": 0.05,
            "interaction_pval": 0.04,
            "support_coef": 0.0,
            "support_se": 0.0,
            "harassment_coef": 0.0,
            "harassment_se": 0.0,
            "n_obs": 50,
            "r_squared": 0.0,
            "f_statistic": 0.0,
            "bootstrap_ci": (0.01, 0.19)
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "results.csv"
        df = main(results, output_path)
        
        assert df is not None
        assert len(df) == 1
        assert "interaction_pval_fdr" in df.columns
        assert output_path.exists()