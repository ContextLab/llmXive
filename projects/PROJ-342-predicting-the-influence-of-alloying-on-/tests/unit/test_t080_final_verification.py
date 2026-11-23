import os
import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = ARTIFACTS_DIR / "reports"
MODELS_DIR = ARTIFACTS_DIR / "models"
METRICS_DIR = ARTIFACTS_DIR / "metrics"

def test_t080_cleaned_data_exists():
    """Verify T014 output: cleaned_mg.csv exists and is non-empty."""
    path = PROCESSED_DIR / "cleaned_mg.csv"
    assert path.exists(), f"{path} does not exist"
    assert path.stat().st_size > 0, f"{path} is empty"

def test_t080_model_artifact_exists():
    """Verify T024a output: best_model.pkl exists and is non-empty."""
    path = MODELS_DIR / "best_model.pkl"
    assert path.exists(), f"{path} does not exist"
    assert path.stat().st_size > 0, f"{path} is empty"

def test_t080_final_report_exists():
    """Verify T050 output: final_report.md exists and is non-empty."""
    path = REPORTS_DIR / "final_report.md"
    assert path.exists(), f"{path} does not exist"
    assert path.stat().st_size > 0, f"{path} is empty"

def test_t080_report_associational_phrase():
    """Verify T049: Report contains mandatory associational phrase."""
    path = REPORTS_DIR / "final_report.md"
    if not path.exists():
        pytest.skip("Report not generated yet")
    
    content = path.read_text()
    assert "These findings are associational only" in content, \
        "Mandatory phrase 'These findings are associational only' not found in report."

def test_t080_vif_diagnostic_log_exists():
    """Verify T083: VIF diagnostic log exists."""
    path = PROCESSED_DIR / "vif_diagnostic_log.json"
    assert path.exists(), f"{path} does not exist"
    with open(path) as f:
        data = json.load(f)
        assert "flagged_features" in data, "Missing 'flagged_features' key"
        assert "vif_values" in data, "Missing 'vif_values' key"

def test_t080_sensitivity_analysis_exists():
    """Verify T083: Sensitivity analysis exists with variance."""
    path = METRICS_DIR / "sensitivity_analysis.json"
    assert path.exists(), f"{path} does not exist"
    with open(path) as f:
        data = json.load(f)
        assert "max_depth_sweep" in data, "Missing 'max_depth_sweep' key"
        assert "r2_variance" in data, "Missing 'r2_variance' key"

def test_t080_collinearity_log_exists():
    """Verify T060a: Collinearity log exists."""
    path = PROCESSED_DIR / "collinearity_log.json"
    assert path.exists(), f"{path} does not exist"
    with open(path) as f:
        data = json.load(f)
        assert "condition_number" in data, "Missing 'condition_number' key"

def test_t080_fdr_pvalues_exists():
    """Verify T034: FDR corrected p-values exist."""
    path = PROCESSED_DIR / "fdr_corrected_pvalues.json"
    assert path.exists(), f"{path} does not exist"
    with open(path) as f:
        data = json.load(f)
        assert "original_pvalues" in data, "Missing 'original_pvalues' key"
        assert "corrected_pvalues" in data, "Missing 'corrected_pvalues' key"
