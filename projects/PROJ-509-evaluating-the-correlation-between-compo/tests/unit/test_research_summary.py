import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the function to test
from generate_research_summary import generate_research_md, load_json_safe, format_float

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    eval_dir = tmp_path / 'data' / 'evaluation'
    eval_dir.mkdir(parents=True)
    return tmp_path

def test_format_float_none():
    """Test that format_float handles None gracefully."""
    assert format_float(None) == "N/A"
    assert format_float(None, 2) == "N/A"

def test_format_float_value():
    """Test that format_float formats floats correctly."""
    assert format_float(1.23456, 2) == "1.23"
    assert format_float(0.0, 4) == "0.0000"
    assert format_float(-5.55555, 3) == "-5.556"

def test_load_json_safe_missing_file(tmp_path):
    """Test load_json_safe returns None for missing file."""
    missing_file = tmp_path / 'nonexistent.json'
    assert load_json_safe(missing_file) is None

def test_load_json_safe_invalid_json(tmp_path):
    """Test load_json_safe returns None for invalid JSON."""
    bad_file = tmp_path / 'bad.json'
    bad_file.write_text("{ invalid json }")
    assert load_json_safe(bad_file) is None

def test_load_json_safe_valid(tmp_path):
    """Test load_json_safe loads valid JSON."""
    good_file = tmp_path / 'good.json'
    data = {"key": "value", "num": 123}
    good_file.write_text(json.dumps(data))
    assert load_json_safe(good_file) == data

def test_generate_research_md_creates_file(temp_dir):
    """Test that generate_research_md creates the output file."""
    output_path = temp_dir / 'research.md'
    
    metrics = {
        'rf_r2': 0.85, 'rf_mae': 0.1, 'rf_rmse': 0.2, 'rf_overfitting_ratio': 0.05,
        'gb_r2': 0.82, 'gb_mae': 0.12, 'gb_rmse': 0.25, 'gb_overfitting_ratio': 0.08
    }
    vif_scores = {'feat1': 2.5, 'feat2': 12.0}
    ale_plots = ['ale_feat1.png', 'ale_feat2.png']
    feature_ranking = [{'feature': 'feat1', 'importance': 0.5}, {'feature': 'feat2', 'importance': 0.3}]
    perm_results = {'correlation': 0.95, 'importance_correlation_pass': True}

    generate_research_md(
        metrics=metrics,
        vif_scores=vif_scores,
        ale_plots=ale_plots,
        feature_ranking=feature_ranking,
        permutation_results=perm_results,
        output_path=output_path
    )

    assert output_path.exists()
    content = output_path.read_text()
    assert "# Research Summary" in content
    assert "0.8500" in content # R2
    assert "ale_feat1.png" in content
    assert "High Collinearity" in content # VIF > 10

def test_generate_research_md_missing_artifacts(temp_dir):
    """Test that generate_research_md handles missing artifacts gracefully."""
    output_path = temp_dir / 'research.md'
    
    # Pass empty/None data
    generate_research_md(
        metrics={},
        vif_scores={},
        ale_plots=[],
        feature_ranking=[],
        permutation_results={},
        output_path=output_path
    )

    assert output_path.exists()
    content = output_path.read_text()
    assert "N/A" in content
    assert "not available" in content.lower()