"""
Unit tests for T028: generate_statistical_report.py
"""
import json
import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from generate_statistical_report import (
    calculate_effect_size,
    extract_sc_metrics,
    generate_final_report,
    load_statistical_results,
    load_baseline_comparison,
    load_divergence_report
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def setup_test_files(temp_dir):
    # Create necessary directories and files
    processed_dir = temp_dir / "data" / "processed"
    processed_dir.mkdir(parents=True)

    # 1. statistical_results.json (from T025)
    stats_data = {
        "p_value": 0.03,
        "effect_size": 0.8,
        "test_type": "permutation_test",
        "bonferroni_adjusted": True
    }
    with open(processed_dir / "statistical_results.json", 'w') as f:
        json.dump(stats_data, f)

    # 2. divergence_report.json (from T024a)
    divergence_data = {
        "is_divergent": False
    }
    with open(processed_dir / "divergence_report.json", 'w') as f:
        json.dump(divergence_data, f)

    # 3. baseline_comparison.csv (from T022)
    df = pd.DataFrame([
        {"condition": "dynamic", "win_rate": 0.85, "avg_tokens": 2500},
        {"condition": "static", "win_rate": 0.82, "avg_tokens": 4000},
        {"condition": "random", "win_rate": 0.50, "avg_tokens": 1000}
    ])
    df.to_csv(processed_dir / "baseline_comparison.csv", index=False)

    # Patch the paths in the module
    with patch('generate_statistical_report.OUTPUT_DIR', processed_dir), \
         patch('generate_statistical_report.OUTPUT_FILE', processed_dir / "statistical_results.json"), \
         patch('generate_statistical_report.BASELINE_COMPARISON_FILE', processed_dir / "baseline_comparison.csv"), \
         patch('generate_statistical_report.DIVERGENCE_REPORT_FILE', processed_dir / "divergence_report.json"):
        yield processed_dir

def test_calculate_effect_size():
    # Standard case
    d = calculate_effect_size(100, 90, 10, 10)
    assert d == pytest.approx(1.0, rel=0.01)

    # Zero std case
    d = calculate_effect_size(100, 90, 0, 0)
    assert d == 0.0

    # Different stds
    d = calculate_effect_size(100, 90, 10, 20)
    # Pooled std = sqrt((100 + 400)/2) = sqrt(250) ~ 15.81
    # d = 10 / 15.81 ~ 0.63
    assert d > 0.5 and d < 0.7

def test_extract_sc_metrics(setup_test_files):
    df = pd.read_csv(setup_test_files / "baseline_comparison.csv")
    metrics = extract_sc_metrics(df)

    assert "sc_001_token_reduction_pct" in metrics
    assert "sc_003_win_rate_diff" in metrics
    
    # Check calculations
    # Tokens: (4000 - 2500) / 4000 = 1500 / 4000 = 0.375 -> 37.5%
    assert abs(metrics["sc_001_token_reduction_pct"] - 37.5) < 0.1
    # Win rate: 0.85 - 0.82 = 0.03
    assert abs(metrics["sc_003_win_rate_diff"] - 0.03) < 0.001

def test_generate_final_report(setup_test_files):
    report = generate_final_report()

    assert "p_value" in report
    assert "effect_size" in report
    assert "test_type" in report
    assert "bonferroni_adjusted" in report
    assert "divergence_status" in report
    assert "sc_metrics" in report
    assert report["divergence_status"] is False
    assert report["p_value"] == 0.03
    
    # Check output file exists
    assert (setup_test_files / "statistical_results.json").exists()

def test_load_statistical_results_missing_file(temp_dir):
    # Ensure the file does not exist
    with pytest.raises(FileNotFoundError):
        load_statistical_results()

def test_load_baseline_comparison_missing_file(temp_dir):
    with pytest.raises(FileNotFoundError):
        load_baseline_comparison()

def test_load_divergence_report_missing_file(temp_dir):
    with pytest.raises(FileNotFoundError):
        load_divergence_report()
