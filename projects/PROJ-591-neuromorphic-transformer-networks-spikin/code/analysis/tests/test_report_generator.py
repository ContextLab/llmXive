import os
import sys
import tempfile
import pandas as pd
import json
import pytest
from analysis.report_generator import generate_report, load_temporal_metrics

@pytest.fixture
def temp_csv_files(tmp_path):
    """Create temporary CSV files for testing."""
    baseline_path = tmp_path / "baseline_metrics.csv"
    spiking_path = tmp_path / "spiking_metrics.csv"
    sensitivity_path = tmp_path / "sensitivity_analysis.csv"
    
    # Create baseline data
    baseline_data = {
        'seed': [1, 2, 3, 4, 5],
        'epoch': [5, 5, 5, 5, 5],
        'perplexity': [15.2, 14.8, 15.5, 14.9, 15.1],
        'energy_per_token_kWh': [0.0001, 0.0001, 0.0001, 0.0001, 0.0001],
        'wall_clock_time': [100, 105, 98, 102, 101]
    }
    pd.DataFrame(baseline_data).to_csv(baseline_path, index=False)
    
    # Create spiking data
    temporal_metrics = [
        json.dumps({'isi_variance': 0.5, 'bits_per_spike': 2.1, 'synchrony': 0.3}),
        json.dumps({'isi_variance': 0.6, 'bits_per_spike': 2.0, 'synchrony': 0.35}),
        json.dumps({'isi_variance': 0.45, 'bits_per_spike': 2.2, 'synchrony': 0.28}),
        json.dumps({'isi_variance': 0.55, 'bits_per_spike': 2.05, 'synchrony': 0.32}),
        json.dumps({'isi_variance': 0.48, 'bits_per_spike': 2.15, 'synchrony': 0.31})
    ]
    
    spiking_data = {
        'seed': [1, 2, 3, 4, 5],
        'epoch': [5, 5, 5, 5, 5],
        'perplexity': [15.8, 15.2, 16.1, 15.4, 15.6],
        'energy_per_token_kWh': [0.00008, 0.00007, 0.00009, 0.00008, 0.000075],
        'wall_clock_time': [120, 125, 118, 122, 121],
        'temporal_coding_metrics': temporal_metrics
    }
    pd.DataFrame(spiking_data).to_csv(spiking_path, index=False)
    
    # Create sensitivity data
    sens_data = {
        'threshold': [0.20, 0.25, 0.30, 0.35],
        'true_positive_rate': [0.9, 0.8, 0.6, 0.4],
        'false_positive_rate': [0.1, 0.15, 0.2, 0.25]
    }
    pd.DataFrame(sens_data).to_csv(sensitivity_path, index=False)
    
    return str(baseline_path), str(spiking_path), str(sensitivity_path)

def test_generate_report_creates_file(tmp_path, temp_csv_files):
    """Test that generate_report creates the output markdown file."""
    baseline, spiking, sensitivity = temp_csv_files
    output_path = tmp_path / "test_report.md"
    
    result = generate_report(
        baseline_path=baseline,
        spiking_path=spiking,
        sensitivity_path=sensitivity,
        output_path=str(output_path)
    )
    
    assert os.path.exists(result)
    assert result == str(output_path)
    
    # Check content
    with open(result, 'r') as f:
        content = f.read()
    
    assert "# Statistical Analysis Report" in content
    assert "Executive Summary" in content
    assert "Performance Metrics" in content
    assert "Temporal Coding Characteristics" in content

def test_generate_report_with_missing_data(tmp_path):
    """Test handling of missing input files."""
    output_path = tmp_path / "test_report_missing.md"
    
    # Should not crash, but report missing data
    result = generate_report(
        baseline_path="nonexistent/baseline.csv",
        spiking_path="nonexistent/spiking.csv",
        output_path=str(output_path)
    )
    
    assert os.path.exists(result)
    with open(result, 'r') as f:
        content = f.read()
    
    assert "CRITICAL NOTE" in content

def test_load_temporal_metrics(tmp_path, temp_csv_files):
    """Test loading and parsing temporal metrics."""
    _, spiking_path, _ = temp_csv_files
    
    df = load_temporal_metrics(spiking_path)
    
    assert 'parsed_temporal' in df.columns
    assert len(df) == 5
    
    # Check if parsing worked
    first_row = df.iloc[0]['parsed_temporal']
    assert isinstance(first_row, dict)
    assert 'isi_variance' in first_row
    assert 'bits_per_spike' in first_row