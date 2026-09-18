import pytest
import math
import os
import sys
import json
from pathlib import Path
import tempfile
import csv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.analysis.statistical_tests import (
    load_metrics_data,
    group_by_source_type,
    calculate_cohens_d,
    perform_independent_t_test,
    run_analysis_for_metric,
    run_statistical_tests
)

# Sample data fixture
SAMPLE_DATA = [
    {"pr_id": 1, "source_type": "llm", "comment_count": 5.0, "time_to_merge_minutes": 100.0, "complexity_score": 10.0},
    {"pr_id": 2, "source_type": "llm", "comment_count": 6.0, "time_to_merge_minutes": 120.0, "complexity_score": 12.0},
    {"pr_id": 3, "source_type": "llm", "comment_count": 4.0, "time_to_merge_minutes": 90.0, "complexity_score": 8.0},
    {"pr_id": 4, "source_type": "human", "comment_count": 10.0, "time_to_merge_minutes": 200.0, "complexity_score": 15.0},
    {"pr_id": 5, "source_type": "human", "comment_count": 12.0, "time_to_merge_minutes": 250.0, "complexity_score": 20.0},
    {"pr_id": 6, "source_type": "human", "comment_count": 9.0, "time_to_merge_minutes": 180.0, "complexity_score": 14.0},
]

@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file with sample data."""
    file_path = tmp_path / "test_metrics.csv"
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["pr_id", "source_type", "comment_count", "time_to_merge_minutes", "complexity_score"])
        writer.writeheader()
        writer.writerows(SAMPLE_DATA)
    return str(file_path)

def test_group_by_source_type():
    """Test that data is correctly split into LLM and Human groups."""
    llm_vals, human_vals = group_by_source_type(SAMPLE_DATA, "comment_count")
    
    assert len(llm_vals) == 3
    assert len(human_vals) == 3
    
    # Check values
    assert set(llm_vals) == {5.0, 6.0, 4.0}
    assert set(human_vals) == {10.0, 12.0, 9.0}

def test_group_by_source_type_missing_metric():
    """Test behavior when metric is missing."""
    data_with_missing = SAMPLE_DATA + [{"pr_id": 7, "source_type": "llm", "comment_count": None, "time_to_merge_minutes": 50.0}]
    llm_vals, human_vals = group_by_source_type(data_with_missing, "comment_count")
    
    # Should skip the None value
    assert len(llm_vals) == 3

def test_calculate_cohens_d():
    """Test Cohen's d calculation with known values."""
    # Group 1: [1, 2, 3] -> mean=2, var=1
    # Group 2: [4, 5, 6] -> mean=5, var=1
    # Pooled var = 1, pooled std = 1
    # d = (2 - 5) / 1 = -3
    g1 = [1.0, 2.0, 3.0]
    g2 = [4.0, 5.0, 6.0]
    
    d = calculate_cohens_d(g1, g2)
    assert math.isclose(d, -3.0, abs_tol=1e-5)

def test_calculate_cohens_d_zero_variance():
    """Test Cohen's d when variance is zero."""
    g1 = [1.0, 1.0, 1.0]
    g2 = [2.0, 2.0, 2.0]
    
    # Pooled std will be 1.0 (diff in means) / 0? No, pooled var is 0.
    # Actually, if both groups have 0 variance, pooled var is 0.
    # The function should return 0.0 or handle gracefully.
    d = calculate_cohens_d(g1, g2)
    # With zero pooled std, our implementation returns 0.0
    assert d == 0.0

def test_perform_independent_t_test():
    """Test t-test function returns expected structure."""
    g1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    g2 = [10.0, 11.0, 12.0, 13.0, 14.0]
    
    result = perform_independent_t_test(g1, g2)
    
    assert "t_statistic" in result
    assert "p_value" in result
    assert isinstance(result["t_statistic"], float)
    assert isinstance(result["p_value"], float)
    assert result["p_value"] < 0.05 # Should be significant

def test_run_analysis_for_metric(temp_csv_file):
    """Test full analysis pipeline for a single metric."""
    result = run_analysis_for_metric(SAMPLE_DATA, "comment_count", alpha=0.05)
    
    assert result["metric"] == "comment_count"
    assert result["status"] != "skipped"
    assert "t_test" in result
    assert "effect_size" in result
    assert "group_sizes" in result
    assert result["group_sizes"]["llm"] == 3
    assert result["group_sizes"]["human"] == 3
    
    # Check significance logic
    assert "significant_at_alpha_0_05" in result["t_test"]

def test_run_statistical_tests_integration(temp_csv_file):
    """Test the main integration function writes output file."""
    output_file = str(Path(temp_csv_file).parent / "results.json")
    
    results = run_statistical_tests(
        input_file=temp_csv_file,
        output_file=output_file,
        alpha=0.05
    )
    
    # Verify file exists
    assert os.path.exists(output_file)
    
    # Verify content
    with open(output_file, 'r') as f:
        saved_results = json.load(f)
    
    assert "config" in saved_results
    assert "results" in saved_results
    assert len(saved_results["results"]) == 2 # comment_count and time_to_merge_minutes
    
    # Check specific metric results
    metrics_found = [r["metric"] for r in saved_results["results"]]
    assert "comment_count" in metrics_found
    assert "time_to_merge_minutes" in metrics_found

def test_insufficient_data_raises_error():
    """Test that running analysis with only one group raises ValueError."""
    single_group_data = [
        {"pr_id": 1, "source_type": "llm", "comment_count": 5.0, "time_to_merge_minutes": 100.0},
    ]
    
    with pytest.raises(ValueError) as exc_info:
        group_by_source_type(single_group_data, "comment_count")
    
    assert "Insufficient data" in str(exc_info.value)