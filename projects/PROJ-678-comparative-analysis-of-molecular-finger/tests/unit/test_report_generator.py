"""
Unit tests for the report generator (T029).

Tests verify that:
1. The report generator correctly loads metrics, stats, and SC-003 results.
2. The markdown table generation works as expected.
3. The final report contains all required sections.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Import the module to test
from report_generator import (
    generate_markdown_table,
    generate_final_report,
    load_metrics_from_disk,
    load_statistical_results,
    load_sc003_results
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_metrics_dir(temp_dir):
    """Create mock metrics files for testing."""
    models_dir = temp_dir / "models"
    models_dir.mkdir()
    
    # Create mock metrics for 2 folds
    for fold_idx in range(2):
        metrics_data = {
            "morgan": {
                "roc_auc": 0.85 + fold_idx * 0.01,
                "pr_auc": 0.80 + fold_idx * 0.01,
                "balanced_accuracy": 0.82 + fold_idx * 0.01
            },
            "maccs": {
                "roc_auc": 0.82 + fold_idx * 0.01,
                "pr_auc": 0.78 + fold_idx * 0.01,
                "balanced_accuracy": 0.79 + fold_idx * 0.01
            }
        }
        metrics_file = models_dir / f"fold_{fold_idx}_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
    
    return models_dir

@pytest.fixture
def mock_stats_dir(temp_dir):
    """Create mock statistical results."""
    stats_dir = temp_dir / "stats"
    stats_dir.mkdir()
    
    stats_data = {
        "roc_auc": {
            "p_value": 0.03,
            "confidence_interval": [0.01, 0.05]
        },
        "pr_auc": {
            "p_value": 0.04,
            "confidence_interval": [0.02, 0.06]
        }
    }
    
    stats_file = stats_dir / "statistical_results.json"
    with open(stats_file, 'w') as f:
        json.dump(stats_data, f)
    
    return stats_dir

@pytest.fixture
def mock_sc003_dir(temp_dir):
    """Create mock SC-003 results."""
    models_dir = temp_dir / "models"
    models_dir.mkdir()
    
    sc003_data = {
        "morgan_gini_sum": 0.12,
        "maccs_gini_sum": 0.08,
        "threshold": 0.15,
        "passed": True
    }
    
    sc003_file = models_dir / "sc003_analysis.json"
    with open(sc003_file, 'w') as f:
        json.dump(sc003_data, f)
    
    return models_dir

def test_generate_markdown_table():
    """Test markdown table generation."""
    data = [
        {"Fold": 1, "ROC-AUC": 0.85, "PR-AUC": 0.80},
        {"Fold": 2, "ROC-AUC": 0.86, "PR-AUC": 0.81}
    ]
    columns = ["Fold", "ROC-AUC", "PR-AUC"]
    
    table = generate_markdown_table(data, columns, "Test Table")
    
    assert "### Test Table" in table
    assert "| Fold | ROC-AUC | PR-AUC |" in table
    assert "|---|---|---|" in table
    assert "| 1 | 0.85 | 0.80 |" in table
    assert "| 2 | 0.86 | 0.81 |" in table

def test_generate_markdown_table_empty():
    """Test markdown table generation with empty data."""
    data = []
    columns = ["Fold", "ROC-AUC"]
    
    table = generate_markdown_table(data, columns, "Empty Table")
    
    assert "### Empty Table" in table
    assert "No data available" in table

def test_load_metrics_from_disk(mock_metrics_dir):
    """Test loading metrics from disk."""
    metrics = load_metrics_from_disk(mock_metrics_dir, n_folds=2)
    
    assert 'morgan' in metrics
    assert 'maccs' in metrics
    assert len(metrics['morgan']) == 2
    assert len(metrics['maccs']) == 2
    
    # Check values
    assert metrics['morgan'][0]['roc_auc'] == 0.85
    assert metrics['maccs'][0]['roc_auc'] == 0.82

def test_load_statistical_results(mock_stats_dir):
    """Test loading statistical results."""
    stats = load_statistical_results(mock_stats_dir)
    
    assert 'roc_auc' in stats
    assert 'pr_auc' in stats
    assert stats['roc_auc']['p_value'] == 0.03
    assert stats['pr_auc']['p_value'] == 0.04

def test_load_sc003_results(mock_sc003_dir):
    """Test loading SC-003 results."""
    sc003 = load_sc003_results(mock_sc003_dir)
    
    assert 'morgan_gini_sum' in sc003
    assert 'maccs_gini_sum' in sc003
    assert sc003['passed'] is True

def test_generate_final_report(temp_dir, mock_metrics_dir, mock_stats_dir, mock_sc003_dir):
    """Test final report generation."""
    output_path = temp_dir / "research_results.md"
    
    # Mock the directories for the function
    # We need to adjust the function to accept paths directly
    # For now, we'll test the logic by calling generate_final_report with correct paths
    # But since the function expects specific directory structures, we'll create them
    
    # Create the required directory structure
    processed_dir = temp_dir / "data" / "processed"
    models_dir = processed_dir / "models"
    models_dir.mkdir(parents=True)
    
    # Copy mock files to the expected locations
    import shutil
    for file in mock_metrics_dir.glob("*.json"):
        shutil.copy(file, models_dir)
    
    stats_dir = processed_dir
    stats_file = mock_stats_dir / "statistical_results.json"
    shutil.copy(stats_file, stats_dir)
    
    sc003_file = mock_sc003_dir / "sc003_analysis.json"
    shutil.copy(sc003_file, models_dir)
    
    # Generate report
    generate_final_report(output_path, models_dir, stats_dir, n_folds=2)
    
    # Verify report exists and contains expected sections
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        content = f.read()
    
    assert "Comparative Analysis of Molecular Fingerprints" in content
    assert "Performance Metrics by Fold" in content
    assert "Statistical Test Results" in content
    assert "SC-003 Analysis" in content
    assert "Measurement Uncertainty & Calibration" in content
    assert "Conclusion" in content
    
    # Verify specific content
    assert "Morgan Fingerprints" in content
    assert "MACCS Keys" in content
    assert "p-value" in content
    assert "Phosphorus-Centered Feature Importance" in content
    assert "SC-003 PASSED" in content