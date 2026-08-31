import pytest
import json
import os
import tempfile
from pathlib import Path
import numpy as np

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.stats import compute_kolmogorov_smirnov_test, load_json_metrics, KS_TEST_PATH

@pytest.fixture
def sample_baseline_records():
    """Generate sample baseline records for testing."""
    return [
        {'clip_id': 'clip_001', 'consecutive_ssim': 0.95, 'peak_memory': 2.1},
        {'clip_id': 'clip_002', 'consecutive_ssim': 0.92, 'peak_memory': 2.3},
        {'clip_id': 'clip_003', 'consecutive_ssim': 0.89, 'peak_memory': 2.5},
        {'clip_id': 'clip_004', 'consecutive_ssim': 0.91, 'peak_memory': 2.2},
        {'clip_id': 'clip_005', 'consecutive_ssim': 0.88, 'peak_memory': 2.4},
    ]

@pytest.fixture
def sample_flow_records():
    """Generate sample flow records for testing."""
    return [
        {'clip_id': 'clip_001', 'consecutive_ssim': 0.94, 'peak_memory': 1.8},
        {'clip_id': 'clip_002', 'consecutive_ssim': 0.90, 'peak_memory': 1.9},
        {'clip_id': 'clip_003', 'consecutive_ssim': 0.87, 'peak_memory': 2.0},
        {'clip_id': 'clip_004', 'consecutive_ssim': 0.89, 'peak_memory': 1.85},
        {'clip_id': 'clip_005', 'consecutive_ssim': 0.86, 'peak_memory': 1.95},
    ]

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_ks_test_execution(sample_baseline_records, sample_flow_records, temp_output_dir):
    """Test that the K-S test executes correctly and produces valid output."""
    # Override the output path for testing
    import analysis.stats
    original_path = analysis.stats.KS_TEST_PATH
    test_path = os.path.join(temp_output_dir, 'ks_test.json')
    analysis.stats.KS_TEST_PATH = test_path
    
    try:
        result = compute_kolmogorov_smirnov_test(sample_baseline_records, sample_flow_records)
        
        # Verify result structure
        assert 'statistic' in result, "Result missing 'statistic' key"
        assert 'pvalue' in result, "Result missing 'pvalue' key"
        assert isinstance(result['statistic'], float), "Statistic must be a float"
        assert isinstance(result['pvalue'], float), "P-value must be a float"
        assert 0.0 <= result['statistic'] <= 1.0, "Statistic must be between 0 and 1"
        assert 0.0 <= result['pvalue'] <= 1.0, "P-value must be between 0 and 1"
        
        # Verify file was written
        assert os.path.exists(test_path), f"Output file not written to {test_path}"
        
        # Verify file contents match result
        with open(test_path, 'r') as f:
            saved_result = json.load(f)
        
        assert saved_result['statistic'] == result['statistic'], "Saved statistic mismatch"
        assert saved_result['pvalue'] == result['pvalue'], "Saved pvalue mismatch"
        
    finally:
        # Restore original path
        analysis.stats.KS_TEST_PATH = original_path

def test_ks_test_with_nan_values(sample_baseline_records, sample_flow_records, temp_output_dir):
    """Test that K-S test handles NaN values correctly."""
    # Inject NaN values
    sample_baseline_records[0]['consecutive_ssim'] = float('nan')
    sample_flow_records[0]['consecutive_ssim'] = float('inf')
    
    import analysis.stats
    original_path = analysis.stats.KS_TEST_PATH
    test_path = os.path.join(temp_output_dir, 'ks_test_nan.json')
    analysis.stats.KS_TEST_PATH = test_path
    
    try:
        result = compute_kolmogorov_smirnov_test(sample_baseline_records, sample_flow_records)
        
        # Should still produce valid results despite NaN/Inf
        assert 'statistic' in result
        assert 'pvalue' in result
        assert result['baseline_n'] == 4, "Should have filtered out NaN value"
        assert result['flow_n'] == 4, "Should have filtered out Inf value"
        
    finally:
        analysis.stats.KS_TEST_PATH = original_path

def test_ks_test_insufficient_data():
    """Test that K-S test raises error with insufficient data."""
    baseline = [{'clip_id': 'clip_001', 'consecutive_ssim': 0.95}]
    flow = [{'clip_id': 'clip_001', 'consecutive_ssim': 0.94}]
    
    with pytest.raises(ValueError, match="Insufficient data points"):
        compute_kolmogorov_smirnov_test(baseline, flow)

def test_ks_test_empty_data():
    """Test that K-S test raises error with empty data."""
    with pytest.raises(ValueError, match="Cannot perform K-S test with empty record lists"):
        compute_kolmogorov_smirnov_test([], [])

def test_ks_test_file_output(sample_baseline_records, sample_flow_records, temp_output_dir):
    """Test that K-S test writes output to the correct file path."""
    import analysis.stats
    original_path = analysis.stats.KS_TEST_PATH
    test_path = os.path.join(temp_output_dir, 'ks_test_output.json')
    analysis.stats.KS_TEST_PATH = test_path
    
    try:
        result = compute_kolmogorov_smirnov_test(sample_baseline_records, sample_flow_records)
        
        # Verify file exists and is valid JSON
        assert os.path.isfile(test_path)
        with open(test_path, 'r') as f:
            data = json.load(f)
        
        assert 'statistic' in data
        assert 'pvalue' in data
        assert 'description' in data
        assert 'baseline_n' in data
        assert 'flow_n' in data
        
    finally:
        analysis.stats.KS_TEST_PATH = original_path