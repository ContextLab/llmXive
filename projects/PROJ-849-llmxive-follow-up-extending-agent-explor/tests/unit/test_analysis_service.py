"""
Unit tests for analysis_service.py (User Story 2).
"""
import pytest
import json
import tempfile
from pathlib import Path
from scipy.stats import pearsonr

from services.analysis_service import (
    load_divergence_scores,
    load_simulated_failure_rates,
    merge_datasets,
    validate_sample_size,
    compute_pearson_correlation,
    analyze_correlation,
    run_analysis
)


@pytest.fixture
def temp_divergence_file():
    data = [
        {"problem_id": "p1", "semantic_divergence_score": 0.9, "cosine_similarity": 0.1},
        {"problem_id": "p2", "semantic_divergence_score": 0.8, "cosine_similarity": 0.2},
        {"problem_id": "p3", "semantic_divergence_score": 0.7, "cosine_similarity": 0.3},
        {"problem_id": "p4", "semantic_divergence_score": 0.6, "cosine_similarity": 0.4},
        {"problem_id": "p5", "semantic_divergence_score": 0.5, "cosine_similarity": 0.5},
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
    return Path(f.name)


@pytest.fixture
def temp_failure_file():
    data = [
        {"problem_id": "p1", "simulated_failure": True, "simulated_failure_rate": 0.9},
        {"problem_id": "p2", "simulated_failure": True, "simulated_failure_rate": 0.8},
        {"problem_id": "p3", "simulated_failure": False, "simulated_failure_rate": 0.3},
        {"problem_id": "p4", "simulated_failure": False, "simulated_failure_rate": 0.2},
        {"problem_id": "p5", "simulated_failure": False, "simulated_failure_rate": 0.1},
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
    return Path(f.name)


def test_load_divergence_scores(temp_divergence_file):
    data = load_divergence_scores(temp_divergence_file)
    assert len(data) == 5
    assert data[0]["problem_id"] == "p1"
    assert "semantic_divergence_score" in data[0]


def test_load_simulated_failure_rates(temp_failure_file):
    data = load_simulated_failure_rates(temp_failure_file)
    assert len(data) == 5
    assert data[0]["problem_id"] == "p1"
    assert "simulated_failure_rate" in data[0]


def test_merge_datasets(temp_divergence_file, temp_failure_file):
    div_data = load_divergence_scores(temp_divergence_file)
    fail_data = load_simulated_failure_rates(temp_failure_file)
    merged = merge_datasets(div_data, fail_data)

    assert len(merged) == 5
    assert merged[0]["problem_id"] == "p1"
    assert merged[0]["semantic_divergence_score"] == 0.9
    assert merged[0]["simulated_failure_rate"] == 0.9


def test_merge_datasets_missing_keys(temp_divergence_file):
    # Create failure file with missing problem_id
    fail_data = [
        {"problem_id": "p99", "simulated_failure": True, "simulated_failure_rate": 0.9}
    ]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(fail_data, f)
    fail_path = Path(f.name)

    div_data = load_divergence_scores(temp_divergence_file)
    fail_data_loaded = load_simulated_failure_rates(fail_path)

    merged = merge_datasets(div_data, fail_data_loaded)
    assert len(merged) == 0  # No matches


def test_validate_sample_size_pass():
    data = [{"id": i} for i in range(30)]
    validate_sample_size(data, min_n=30)  # Should not raise


def test_validate_sample_size_fail():
    data = [{"id": i} for i in range(29)]
    with pytest.raises(ValueError, match="Insufficient Sample Size"):
        validate_sample_size(data, min_n=30)


def test_compute_pearson_correlation():
    # Create synthetic data with known negative correlation
    # X: 1, 2, 3, 4, 5
    # Y: 5, 4, 3, 2, 1
    data = [
        {"x": 1.0, "y": 5.0},
        {"x": 2.0, "y": 4.0},
        {"x": 3.0, "y": 3.0},
        {"x": 4.0, "y": 2.0},
        {"x": 5.0, "y": 1.0},
    ]

    corr, p_val = compute_pearson_correlation(data, x_key="x", y_key="y")

    # Perfect negative correlation should be -1.0
    assert abs(corr - (-1.0)) < 1e-6
    assert p_val < 0.05  # Should be significant for perfect correlation


def test_analyze_correlation_negative():
    data = [
        {"problem_id": f"p{i}", "semantic_divergence_score": 6-i, "simulated_failure_rate": i}
        for i in range(1, 31)  # N=30
    ]
    # Divergence: 5,4,3,2,1...
    # Failure: 1,2,3,4,5...
    # Negative correlation

    result = analyze_correlation(data, min_n=30)

    assert result["sample_size"] == 30
    assert result["correlation_coefficient"] < 0
    assert result["p_value"] < 0.05
    assert result["is_significant_negative"] is True
    assert result["hypothesis_validated"] is True


def test_run_analysis_full_pipeline(temp_divergence_file, temp_failure_file):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as out_f:
        output_path = Path(out_f.name)

    result = run_analysis(temp_divergence_file, temp_failure_file, output_path)

    assert "correlation_coefficient" in result
    assert "p_value" in result
    assert output_path.exists()

    with open(output_path, 'r') as f:
        saved_result = json.load(f)
    assert saved_result == result

    # Cleanup
    output_path.unlink()
