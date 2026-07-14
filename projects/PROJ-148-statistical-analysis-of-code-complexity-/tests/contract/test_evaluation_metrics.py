"""
Contract test for evaluation metrics (US3).
"""
import pytest
import pandas as pd

def test_evaluation_metrics(metrics_df: pd.DataFrame):
    """
    Contract test: Verify evaluation metrics dataframe structure.
    """
    if metrics_df is None:
        pytest.skip("Metrics fixture not available.")

    required_cols = ["model_type", "roc_auc", "pr_auc", "fdr"]
    missing = set(required_cols) - set(metrics_df.columns)
    assert not missing, f"Metrics missing columns: {missing}"
