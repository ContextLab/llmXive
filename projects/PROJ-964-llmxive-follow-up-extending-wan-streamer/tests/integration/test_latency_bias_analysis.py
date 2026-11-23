import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture
def sample_hybrid_output(tmp_path):
    """Create a sample hybrid output parquet file for testing."""
    # Create sample data
    n_samples = 1000
    data = {
        'frame_id': range(n_samples),
        'timestamp': np.random.uniform(0, 1000, n_samples),
        'audio_energy': np.random.uniform(0, 50, n_samples),
        'latency_ms': np.random.uniform(10, 100, n_samples),
        'is_skipped': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'turn_label': np.random.choice(['speaker', 'listener'], n_samples),
        'propensity_score': np.random.uniform(0, 1, n_samples)
    }
    
    df = pd.DataFrame(data)
    output_path = tmp_path / "hybrid_output.parquet"
    df.to_parquet(output_path)
    
    return str(output_path)

@pytest.fixture
def expected_output_path(tmp_path):
    """Return expected output path."""
    return str(tmp_path / "latency_bootstrap_results.csv")

def test_latency_bias_analysis_executes(sample_hybrid_output, expected_output_path):
    """Test that the latency bias analysis script executes without errors."""
    script_path = PROJECT_ROOT / "code" / "inference" / "analyze_latency_bias.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path), '--input', sample_hybrid_output, '--output', expected_output_path],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    
    assert result.returncode == 0, f"Script failed with stderr: {result.stderr}"
    assert os.path.exists(expected_output_path), "Output file was not created"

def test_latency_bias_analysis_output_schema(sample_hybrid_output, expected_output_path):
    """Test that the output CSV has the expected schema."""
    script_path = PROJECT_ROOT / "code" / "inference" / "analyze_latency_bias.py"
    
    subprocess.run(
        [sys.executable, str(script_path), '--input', sample_hybrid_output, '--output', expected_output_path],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        check=True
    )
    
    df = pd.read_csv(expected_output_path)
    
    expected_columns = [
        'treatment_effect_mean',
        'treatment_effect_std',
        'ci_lower_95',
        'ci_upper_95',
        't_statistic',
        'p_value',
        'cohens_d',
        'n_treated',
        'n_control',
        'n_bootstrap_samples',
        'data_source',
        'covariates_used',
        'timestamp'
    ]
    
    for col in expected_columns:
        assert col in df.columns, f"Missing expected column: {col}"

def test_latency_bias_analysis_results_validity(sample_hybrid_output, expected_output_path):
    """Test that the analysis produces valid numerical results."""
    script_path = PROJECT_ROOT / "code" / "inference" / "analyze_latency_bias.py"
    
    subprocess.run(
        [sys.executable, str(script_path), '--input', sample_hybrid_output, '--output', expected_output_path],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        check=True
    )
    
    df = pd.read_csv(expected_output_path)
    
    # Check that numerical values are within reasonable bounds
    assert df['treatment_effect_mean'].iloc[0] is not None
    assert df['t_statistic'].iloc[0] is not None
    assert df['p_value'].iloc[0] is not None
    assert 0 <= df['p_value'].iloc[0] <= 1, "P-value should be between 0 and 1"
    
    # Check that sample sizes are positive
    assert df['n_treated'].iloc[0] > 0
    assert df['n_control'].iloc[0] > 0
    assert df['n_bootstrap_samples'].iloc[0] > 0

def test_latency_bias_analysis_with_missing_columns(tmp_path):
    """Test handling of missing columns in input data."""
    # Create sample data without some expected columns
    n_samples = 100
    data = {
        'frame_id': range(n_samples),
        'latency_ms': np.random.uniform(10, 100, n_samples),
        'is_skipped': np.random.choice([0, 1], n_samples)
    }
    
    df = pd.DataFrame(data)
    input_path = tmp_path / "hybrid_output.parquet"
    df.to_parquet(input_path)
    
    output_path = tmp_path / "latency_bootstrap_results.csv"
    
    script_path = PROJECT_ROOT / "code" / "inference" / "analyze_latency_bias.py"
    
    result = subprocess.run(
        [sys.executable, str(script_path), '--input', str(input_path), '--output', str(output_path)],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    
    # Should still execute (using default covariates)
    assert result.returncode == 0 or "No suitable covariates found" in result.stdout