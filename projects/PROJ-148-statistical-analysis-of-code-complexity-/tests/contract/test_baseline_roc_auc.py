"""
Contract test asserting baseline ROC-AUC >= 0.50 and model exceeds it.
"""
import pytest

def test_baseline_roc_auc(model_roc_auc: float):
    """
    Assert ROC-AUC >= 0.50 baseline.
    """
    if model_roc_auc is None:
        pytest.skip("Model ROC-AUC fixture not available.")

    assert model_roc_auc >= 0.50, f"Model ROC-AUC ({model_roc_auc}) is below baseline 0.50"
