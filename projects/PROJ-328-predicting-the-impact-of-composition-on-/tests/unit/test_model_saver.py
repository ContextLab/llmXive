"""
Unit tests for the model_saver module (T031).
Verifies that model artifacts, metrics, and diagnostics are saved correctly
and that FR-007 associational framing warnings are included.
"""
import os
import sys
import json
import yaml
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.model_saver import (
    save_model,
    save_metrics,
    save_vif_results,
    save_shap_summary,
    save_comparison_report,
    save_all_artifacts
)
from config import get_models_dir, get_data_processed_dir

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_base = tempfile.mkdtemp()
    temp_models = Path(temp_base) / "models"
    temp_processed = Path(temp_base) / "data" / "processed"
    temp_models.mkdir(parents=True, exist_ok=True)
    temp_processed.mkdir(parents=True, exist_ok=True)
    
    # Mock config functions to use temp dirs
    original_get_models_dir = get_models_dir
    original_get_data_processed_dir = get_data_processed_dir
    
    def mock_get_models_dir():
        return temp_models
    
    def mock_get_data_processed_dir():
        return temp_processed
    
    # Patch the functions (this is a simple mock for testing)
    import models.model_saver as saver_module
    saver_module.get_models_dir = mock_get_models_dir
    saver_module.get_data_processed_dir = mock_get_data_processed_dir
    
    yield {
        'models': temp_models,
        'processed': temp_processed
    }
    
    # Cleanup
    shutil.rmtree(temp_base)
    # Restore original functions
    saver_module.get_models_dir = original_get_models_dir
    saver_module.get_data_processed_dir = original_get_data_processed_dir

def test_save_model(temp_dirs):
    """Test that a model can be saved and loaded."""
    # Create a simple mock model
    mock_model = {"type": "mock_model", "params": {"n_estimators": 100}}
    
    model_path = save_model(mock_model, "test_model", temp_dirs['models'])
    
    assert model_path.exists()
    assert model_path.suffix == ".pkl"
    
    # Load and verify
    with open(model_path, 'rb') as f:
        import pickle
        loaded_model = pickle.load(f)
    
    assert loaded_model == mock_model

def test_save_metrics_with_framing_warning(temp_dirs):
    """Test that metrics are saved with FR-007 associational framing warning."""
    metrics = {
        "r2": 0.85,
        "rmse": 12.3,
        "mae": 8.5
    }
    
    metrics_path = save_metrics(metrics, "test_model", temp_dirs['processed'])
    
    assert metrics_path.exists()
    assert metrics_path.suffix == ".yaml"
    
    with open(metrics_path, 'r') as f:
        saved_metrics = yaml.safe_load(f)
    
    assert "associational_framing_warning" in saved_metrics
    assert "causal" not in saved_metrics.get("associational_framing_warning", "").lower() or "not causal" in saved_metrics.get("associational_framing_warning", "").lower()
    assert "associational" in saved_metrics.get("associational_framing_warning", "").lower()

def test_save_vif_results(temp_dirs):
    """Test that VIF results are saved correctly."""
    vif_results = [
        {"feature": "element_A", "vif": 1.2, "is_collinear": False},
        {"feature": "element_B", "vif": 6.5, "is_collinear": True}
    ]
    
    vif_path = save_vif_results(vif_results, temp_dirs['processed'])
    
    assert vif_path.exists()
    assert vif_path.suffix == ".yaml"
    
    with open(vif_path, 'r') as f:
        saved_vif = yaml.safe_load(f)
    
    assert isinstance(saved_vif, list)
    assert len(saved_vif) == 2
    assert saved_vif[0]["feature"] == "element_A"

def test_save_shap_summary(temp_dirs):
    """Test that SHAP summary is saved correctly."""
    shap_summary = [
        {"feature": "element_A", "mean_abs_shap": 0.45, "rank": 1},
        {"feature": "element_B", "mean_abs_shap": 0.32, "rank": 2}
    ]
    
    shap_path = save_shap_summary(shap_summary, temp_dirs['processed'])
    
    assert shap_path.exists()
    assert shap_path.suffix == ".yaml"
    
    with open(shap_path, 'r') as f:
        saved_shap = yaml.safe_load(f)
    
    assert isinstance(saved_shap, list)
    assert saved_shap[0]["rank"] == 1

def test_save_comparison_report_with_framing_warning(temp_dirs):
    """Test that comparison report includes FR-007 associational framing warning."""
    comparison_report = {
        "xgboost_r2": 0.85,
        "linear_r2": 0.72,
        "winner": "xgboost",
        "p_value": 0.03
    }
    
    report_path = save_comparison_report(comparison_report, temp_dirs['processed'])
    
    assert report_path.exists()
    assert report_path.suffix == ".yaml"
    
    with open(report_path, 'r') as f:
        saved_report = yaml.safe_load(f)
    
    assert "associational_framing_warning" in saved_report
    assert "not causal" in saved_report.get("associational_framing_warning", "").lower()

def test_save_all_artifacts(temp_dirs):
    """Test that all artifacts are saved in one call."""
    mock_xgb_model = {"type": "xgboost"}
    mock_lin_model = {"type": "linear"}
    
    xgb_metrics = {"r2": 0.85, "rmse": 12.3}
    lin_metrics = {"r2": 0.72, "rmse": 15.1}
    
    vif_results = [{"feature": "A", "vif": 1.2, "is_collinear": False}]
    shap_summary = [{"feature": "A", "mean_abs_shap": 0.45, "rank": 1}]
    comparison_report = {"xgboost_r2": 0.85, "linear_r2": 0.72}
    
    results = save_all_artifacts(
        xgboost_model=mock_xgb_model,
        linear_model=mock_lin_model,
        xgboost_metrics=xgb_metrics,
        linear_metrics=lin_metrics,
        vif_results=vif_results,
        shap_summary=shap_summary,
        comparison_report=comparison_report
    )
    
    # Verify all files exist
    assert 'xgboost_model' in results
    assert 'linear_model' in results
    assert 'xgboost_metrics' in results
    assert 'linear_metrics' in results
    assert 'vif_report' in results
    assert 'shap_ranking' in results
    assert 'comparison_report' in results
    
    for key, path in results.items():
        assert path.exists(), f"Missing artifact: {key} at {path}"
    
    # Verify FR-007 warnings in metrics and comparison report
    with open(results['xgboost_metrics'], 'r') as f:
        xgb_m = yaml.safe_load(f)
        assert "associational_framing_warning" in xgb_m
    
    with open(results['comparison_report'], 'r') as f:
        comp_r = yaml.safe_load(f)
        assert "associational_framing_warning" in comp_r
