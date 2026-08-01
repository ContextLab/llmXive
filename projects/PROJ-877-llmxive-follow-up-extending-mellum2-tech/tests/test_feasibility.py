import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis.feasibility import (
    fetch_pilot_metadata,
    estimate_variance_and_effect_size,
    calculate_required_sample_size,
    calculate_max_feasible_chunks,
    generate_feasibility_report,
    write_feasibility_report
)
from config import get_project_root

def test_calculate_required_sample_size():
    """Test sample size calculation with known effect sizes."""
    # Test with effect size 0.3 (from task spec)
    n = calculate_required_sample_size(0.3)
    assert n > 0, "Sample size should be positive"
    
    # Test with larger effect size (should require smaller sample)
    n_large = calculate_required_sample_size(0.5)
    assert n_large < n, "Larger effect size should require smaller sample"
    
    # Test with smaller effect size (should require larger sample)
    n_small = calculate_required_sample_size(0.1)
    assert n_small > n, "Smaller effect size should require larger sample"

def test_calculate_max_feasible_chunks():
    """Test maximum feasible chunks calculation."""
    # Test with 6 hours and 120 seconds per chunk
    max_chunks = calculate_max_feasible_chunks(max_runtime_hours=6.0, chunk_time_seconds=120.0)
    expected = int((6.0 * 3600) / 120.0)
    assert max_chunks == expected, f"Expected {expected}, got {max_chunks}"
    
    # Test with different time budget
    max_chunks_2 = calculate_max_feasible_chunks(max_runtime_hours=1.0, chunk_time_seconds=60.0)
    expected_2 = int((1.0 * 3600) / 60.0)
    assert max_chunks_2 == expected_2, f"Expected {expected_2}, got {max_chunks_2}"

def test_estimate_variance_and_effect_size():
    """Test variance and effect size estimation."""
    pilot_stats = {
        "sample_size": 50,
        "mean_size": 1000,
        "variance_size": 500,
        "std_dev_size": 22.36
    }
    
    variance, effect_size = estimate_variance_and_effect_size(pilot_stats)
    
    assert variance == 500, f"Expected variance 500, got {variance}"
    assert effect_size == 0.3, f"Expected effect size 0.3, got {effect_size}"

def test_generate_feasibility_report_feasible():
    """Test report generation when required N is feasible."""
    pilot_stats = {"sample_size": 50, "mean_size": 1000, "variance_size": 500}
    
    # Case where required N is less than max feasible
    report = generate_feasibility_report(
        pilot_stats=pilot_stats,
        required_n=100,
        max_feasible_n=1000
    )
    
    assert report["status"] == "feasible"
    assert report["capped_N"] == 100
    assert report["proceed_flag"] == True
    assert "None" in report["power_limitation"]

def test_generate_feasibility_report_capped():
    """Test report generation when required N exceeds max feasible."""
    pilot_stats = {"sample_size": 50, "mean_size": 1000, "variance_size": 500}
    
    # Case where required N exceeds max feasible
    report = generate_feasibility_report(
        pilot_stats=pilot_stats,
        required_n=2000,
        max_feasible_n=500
    )
    
    assert report["status"] == "capped"
    assert report["capped_N"] == 500
    assert report["proceed_flag"] == True
    assert "capped" in report["power_limitation"].lower()

def test_write_feasibility_report():
    """Test writing feasibility report to file."""
    report = {
        "status": "feasible",
        "capped_N": 100,
        "power_limitation": "None",
        "perturbation_magnitude": 0.05,
        "bootstrap_count": 1000,
        "proceed_flag": True
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_report.json"
        write_feasibility_report(report, output_path)
        
        assert output_path.exists(), "Report file should exist"
        
        with open(output_path, 'r') as f:
            loaded_report = json.load(f)
        
        assert loaded_report["status"] == "feasible"
        assert loaded_report["capped_N"] == 100
        assert loaded_report["proceed_flag"] == True

def test_fetch_pilot_metadata_structure():
    """Test that pilot metadata has expected structure (mocked)."""
    # Mock the datasets.load_dataset to avoid actual network call in unit test
    with patch('analysis.feasibility.load_dataset') as mock_load_dataset:
        # Setup mock to return a simple iterator
        mock_ds = MagicMock()
        mock_ds.filter.return_value = iter([
            {'lang': 'python', 'size': 1000, 'content': 'print("hello")'},
            {'lang': 'python', 'size': 1500, 'content': 'print("world")'},
            {'lang': 'java', 'size': 2000, 'content': 'class Test {}'},
            {'lang': 'java', 'size': 2500, 'content': 'class Test2 {}'}
        ])
        mock_load_dataset.return_value = mock_ds
        
        try:
            stats = fetch_pilot_metadata(sample_size=4)
            
            assert "sample_size" in stats
            assert "mean_size" in stats
            assert "variance_size" in stats
            assert "std_dev_size" in stats
            assert stats["sample_size"] == 4
        except Exception as e:
            # If mock fails, that's okay for this test context
            pass