"""
Unit tests for the comparative report generation (T031b).
"""
import json
import pytest
from pathlib import Path
import tempfile
import os

# Import the function to test
import sys
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from analysis.comparative_report import generate_report_content, load_json_file


@pytest.fixture
def sample_metrics():
    return {
        "gnn": {"rmse": 0.5, "mae": 0.4, "r2": 0.85},
        "rf_baseline": {"rmse": 0.6, "mae": 0.5, "r2": 0.75},
        "p_value": 0.03,
        "cohens_d": 0.8,
        "is_proxy_target": False
    }

@pytest.fixture
def sample_rf_importance():
    return [
        {"feature": "MW", "mean_abs_shap": 0.45},
        {"feature": "logP", "mean_abs_shap": 0.35},
        {"feature": "TPSA", "mean_abs_shap": 0.20}
    ]

@pytest.fixture
def sample_gnne_importance():
    return [
        {"substructure": "Aromatic Ring", "importance_score": 0.60},
        {"substructure": "Aliphatic Chain", "importance_score": 0.40},
        {"substructure": "Hydroxyl Group", "importance_score": 0.30}
    ]

@pytest.fixture
def sample_mapping_data():
    return {
        "unique_gnn_features": [
            {
                "substructure": "Complex Aromatic System",
                "gnn_score": 0.55,
                "rf_correlation": 0.15,
                "insight": "Captures aromatic stacking not in MW."
            }
        ]
    }

def test_generate_report_content_includes_header(sample_metrics, sample_rf_importance, sample_gnne_importance, sample_mapping_data):
    """Test that the report includes the main header."""
    content = generate_report_content(
        sample_mapping_data, sample_rf_importance, sample_gnne_importance, sample_metrics, "experimental"
    )
    assert "# Comparative Analysis Report" in content
    assert "Target Variable: Experimental" in content

def test_generate_report_content_includes_metrics_table(sample_metrics, sample_rf_importance, sample_gnne_importance, sample_mapping_data):
    """Test that the report includes the metrics table."""
    content = generate_report_content(
        sample_mapping_data, sample_rf_importance, sample_gnne_importance, sample_metrics, "experimental"
    )
    assert "| Model | RMSE | MAE | R² |" in content
    assert "GNN" in content
    assert "RF Baseline" in content

def test_generate_report_content_includes_statistical_significance(sample_metrics, sample_rf_importance, sample_gnne_importance, sample_mapping_data):
    """Test that the report includes statistical significance section."""
    content = generate_report_content(
        sample_mapping_data, sample_rf_importance, sample_gnne_importance, sample_metrics, "experimental"
    )
    assert "p-value" in content
    assert "Cohen's d" in content

def test_generate_report_content_includes_unique_features(sample_metrics, sample_rf_importance, sample_gnne_importance, sample_mapping_data):
    """Test that the report includes the unique GNN features section."""
    content = generate_report_content(
        sample_mapping_data, sample_rf_importance, sample_gnne_importance, sample_metrics, "experimental"
    )
    assert "Unique GNN-Identified Substructures" in content
    assert "Complex Aromatic System" in content

def test_generate_report_content_proxy_mode(sample_metrics, sample_rf_importance, sample_gnne_importance, sample_mapping_data):
    """Test that the report correctly identifies proxy mode."""
    metrics_proxy = sample_metrics.copy()
    metrics_proxy["is_proxy_target"] = True
    
    content = generate_report_content(
        sample_mapping_data, sample_rf_importance, sample_gnne_importance, metrics_proxy, "proxy (logP)"
    )
    assert "Target Variable: Proxy (logP)" in content

def test_load_json_file_success(tmp_path):
    """Test loading a valid JSON file."""
    test_file = tmp_path / "test.json"
    test_file.write_text('{"key": "value"}')
    
    result = load_json_file(test_file)
    assert result == {"key": "value"}

def test_load_json_file_missing(tmp_path):
    """Test loading a missing JSON file raises error."""
    missing_file = tmp_path / "missing.json"
    
    with pytest.raises(FileNotFoundError):
        load_json_file(missing_file)
