"""
Unit tests for T021b: threshold_identification_raw.py
"""
import csv
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.threshold_identification_raw import (
    load_mc_results,
    aggregate_by_theta,
    prepare_threshold_data
)

@pytest.fixture
def sample_csv_data():
    """Generate a temporary CSV file with sample Monte Carlo results."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(['run_id', 'N', 'theta', 'seed', 'outlier_count', 'max_eigenvalue'])
        # Theta = 1.5 (below threshold expected)
        writer.writerow(['run_1', 1000, 1.5, 42, 0, 1.98])
        writer.writerow(['run_2', 1000, 1.5, 43, 0, 1.99])
        writer.writerow(['run_3', 1000, 1.5, 44, 1, 2.05]) # One outlier
        
        # Theta = 2.5 (above threshold expected)
        writer.writerow(['run_4', 1000, 2.5, 45, 1, 2.45])
        writer.writerow(['run_5', 1000, 2.5, 46, 1, 2.55])
        writer.writerow(['run_6', 1000, 2.5, 47, 1, 2.60])
        
        # Theta = 2.0 (boundary)
        writer.writerow(['run_7', 1000, 2.0, 48, 0, 2.01])
        writer.writerow(['run_8', 1000, 2.0, 49, 1, 2.02])
        
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_mc_results(sample_csv_data):
    """Test that load_mc_results correctly parses the CSV."""
    results = load_mc_results(Path(sample_csv_data))
    assert len(results) == 8
    assert results[0]['theta'] == 1.5
    assert results[0]['outlier_count'] == 0
    assert results[3]['theta'] == 2.5
    assert results[3]['outlier_count'] == 1

def test_aggregate_by_theta(sample_csv_data):
    """Test aggregation logic."""
    results = load_mc_results(Path(sample_csv_data))
    aggregated = aggregate_by_theta(results)
    
    assert len(aggregated) == 3
    assert 1.5 in aggregated
    assert 2.0 in aggregated
    assert 2.5 in aggregated
    
    # Check 1.5 stats
    agg_15 = aggregated[1.5]
    assert agg_15['total_runs'] == 3
    assert agg_15['total_outliers'] == 1
    assert abs(agg_15['outlier_probability'] - (1/3)) < 1e-6
    assert abs(agg_15['avg_max_eigenvalue'] - (1.98+1.99+2.05)/3) < 1e-6
    
    # Check 2.5 stats
    agg_25 = aggregated[2.5]
    assert agg_25['total_runs'] == 3
    assert agg_25['total_outliers'] == 3
    assert agg_25['outlier_probability'] == 1.0

def test_prepare_threshold_data(sample_csv_data):
    """Test final data preparation and structure."""
    results = load_mc_results(Path(sample_csv_data))
    aggregated = aggregate_by_theta(results)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'test_output.json'
        output_data = prepare_threshold_data(aggregated, output_path)
        
        assert 'metadata' in output_data
        assert 'aggregated_by_theta' in output_data
        assert 'summary' in output_data
        
        assert output_data['metadata']['total_simulations'] == 8
        assert output_data['summary']['num_theta_points'] == 3
        assert output_data['summary']['theta_range'] == [1.5, 2.5]
        
        # Verify JSON serialization
        with open(output_path, 'w') as f:
            json.dump(output_data, f)
        
        # Verify file is valid JSON
        with open(output_path, 'r') as f:
            loaded = json.load(f)
            assert loaded['metadata']['total_simulations'] == 8