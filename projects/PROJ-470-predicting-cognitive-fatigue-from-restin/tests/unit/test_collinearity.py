"""Tests for T024: Collinearity diagnostics (VIF)."""
import os
import sys
import json
import tempfile
import shutil
import pandas as pd
import numpy as np

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from collinearity import calculate_vif, load_analysis_results, run_collinearity_diagnostics


def test_calculate_vif_basic():
    """Test VIF calculation with simple data."""
    # Create a DataFrame with no collinearity
    np.random.seed(42)
    n = 100
    data = {
        'Fatigue_Delta': np.random.randn(n),
        'Pre_Complexity': np.random.randn(n),
        'age': np.random.randn(n)
    }
    df = pd.DataFrame(data)

    # Make them orthogonal (no collinearity)
    # In reality, random data has low VIF.
    vif_results = calculate_vif(df)

    assert 'Fatigue_Delta' in vif_results
    assert 'Pre_Complexity' in vif_results
    assert 'age' in vif_results

    # VIF should be close to 1 for uncorrelated variables
    for vif_val in vif_results.values():
        assert vif_val < 2.0, f"VIF {vif_val} unexpectedly high for uncorrelated data"


def test_calculate_vif_collinear():
    """Test VIF calculation with highly collinear data."""
    n = 100
    np.random.seed(42)
    x1 = np.random.randn(n)
    # x2 is highly correlated with x1
    x2 = x1 * 0.99 + np.random.randn(n) * 0.01

    data = {
        'Fatigue_Delta': x1,
        'Pre_Complexity': x2,
        'age': np.random.randn(n)
    }
    df = pd.DataFrame(data)

    vif_results = calculate_vif(df)

    # VIF for correlated variables should be high
    assert vif_results['Fatigue_Delta'] > 5.0 or vif_results['Pre_Complexity'] > 5.0


def test_run_collinearity_diagnostics_pass(tmp_path):
    """Test that run_collinearity_diagnostics passes when VIF < 5."""
    # Create temp data
    n = 100
    np.random.seed(42)
    df_data = {
        'participant_id': [f'sub_{i}' for i in range(n)],
        'Fatigue_Delta': np.random.randn(n),
        'Pre_Complexity': np.random.randn(n),
        'age': np.random.randn(n)
    }
    df = pd.DataFrame(df_data)

    # Save to temp CSVs
    complexity_file = tmp_path / "complexity_metrics.csv"
    delta_file = tmp_path / "delta_scores.csv"
    log_file = tmp_path / "vif_diagnostics.log"
    output_json = tmp_path / "vif_valid_predictors.json"

    # Mock complexity data (simplified)
    complexity_df = pd.DataFrame({
        'participant_id': df['participant_id'],
        'timepoint': 'pre',
        'lzc_value': df['Pre_Complexity']
    })
    complexity_df.to_csv(complexity_file, index=False)

    # Mock delta data
    delta_df = pd.DataFrame({
        'participant_id': df['participant_id'],
        'Fatigue_Delta': df['Fatigue_Delta'],
        'age': df['age']
    })
    delta_df.to_csv(delta_file, index=False)

    # Run diagnostics
    try:
        run_collinearity_diagnostics(
            config={},
            complexity_file=str(complexity_file),
            delta_file=str(delta_file),
            log_file=str(log_file),
            output_json=str(output_json)
        )
    except SystemExit as e:
        # Should not exit with error if VIF < 5
        assert e.code == 0

    # Check output files
    assert log_file.exists()
    assert output_json.exists()

    with open(output_json, 'r') as f:
        result = json.load(f)
    assert 'valid_predictors' in result
    assert len(result['valid_predictors']) > 0


def test_run_collinearity_diagnostics_fail(tmp_path):
    """Test that run_collinearity_diagnostics fails when VIF >= 5."""
    # Create collinear data
    n = 100
    np.random.seed(42)
    x1 = np.random.randn(n)
    x2 = x1 * 0.999 + np.random.randn(n) * 0.001 # Very high correlation

    df_data = {
        'participant_id': [f'sub_{i}' for i in range(n)],
        'Fatigue_Delta': x1,
        'Pre_Complexity': x2,
        'age': np.random.randn(n)
    }
    df = pd.DataFrame(df_data)

    # Save to temp CSVs
    complexity_file = tmp_path / "complexity_metrics.csv"
    delta_file = tmp_path / "delta_scores.csv"
    log_file = tmp_path / "vif_diagnostics.log"
    output_json = tmp_path / "vif_valid_predictors.json"

    # Mock complexity data
    complexity_df = pd.DataFrame({
        'participant_id': df['participant_id'],
        'timepoint': 'pre',
        'lzc_value': df['Pre_Complexity']
    })
    complexity_df.to_csv(complexity_file, index=False)

    # Mock delta data
    delta_df = pd.DataFrame({
        'participant_id': df['participant_id'],
        'Fatigue_Delta': df['Fatigue_Delta'],
        'age': df['age']
    })
    delta_df.to_csv(delta_file, index=False)

    # Run diagnostics - should raise SystemExit(1)
    with pytest.raises(SystemExit) as excinfo:
        run_collinearity_diagnostics(
            config={},
            complexity_file=str(complexity_file),
            delta_file=str(delta_file),
            log_file=str(log_file),
            output_json=str(output_json)
        )
    assert excinfo.value.code == 1

    # Check log file contains error message
    assert log_file.exists()
    with open(log_file, 'r') as f:
        log_content = f.read()
    assert "Collinearity violation" in log_content

    # Output JSON should NOT be created or be empty/invalid if failure occurred
    # The spec says: "If all predictors pass ... output ... vif_valid_predictors.json"
    # So if it fails, we don't expect a valid output file.
    if output_json.exists():
        with open(output_json, 'r') as f:
            result = json.load(f)
        # It might exist but be empty or partial, but the test ensures the script halted.
        # The main verification is the exit code and log content.