import pytest
import json
import csv
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.logging_config import get_logger
from code_04_evaluation_loader import (
    ensure_results_dir,
    load_generated_proposals,
    strip_metadata_for_blinding,
    create_blinded_pairs,
    save_blinded_pairs,
    generate_ratings_template,
    validate_ratings_schema,
    generate_mock_ratings_for_testing,
    ingest_ratings
)
from code_05_statistical_analysis import (
    load_ratings,
    calculate_irr,
    check_normality,
    remove_outliers_iqr,
    perform_statistical_test,
    calculate_validity_improvement,
    run_power_analysis
)
from utils.error_handling import IRRGateFailError

logger = get_logger("test_evaluation")

@pytest.fixture
def sample_proposals():
    return [
        {"id": "1", "problem_statement": "A", "proposal_text": "P1", "group": "pattern-guided"},
        {"id": "2", "problem_statement": "A", "proposal_text": "B1", "group": "baseline"},
        {"id": "3", "problem_statement": "B", "proposal_text": "P2", "group": "pattern-guided"},
        {"id": "4", "problem_statement": "B", "proposal_text": "B2", "group": "baseline"},
    ]

def test_blinding_removes_metadata(sample_proposals, tmp_path):
    pairs = create_blinded_pairs(sample_proposals)
    assert len(pairs) == 2
    for pa, pb in pairs:
        assert "problem_statement" not in pa
        assert "proposal_text" in pa
        assert "group" not in pa

def test_mock_ratings_generation(tmp_path):
    filepath = tmp_path / "test_ratings.csv"
    generate_mock_ratings_for_testing(num_pairs=5, num_experts=2, filepath=str(filepath))
    assert filepath.exists()
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 10  # 5 pairs * 2 experts

def test_irr_gate_passes_on_mock_data(tmp_path):
    generate_mock_ratings_for_testing(num_pairs=10, num_experts=3, filepath=str(tmp_path / "ratings.csv"))
    ratings = ingest_ratings(str(tmp_path / "ratings.csv"))
    irr = calculate_irr(ratings)
    assert irr >= 0.6

def test_statistical_test_runs(tmp_path):
    generate_mock_ratings_for_testing(num_pairs=10, num_experts=3, filepath=str(tmp_path / "ratings.csv"))
    ratings = ingest_ratings(str(tmp_path / "ratings.csv"))
    group_a = [float(r["proposal_a_score"]) for r in ratings]
    group_b = [float(r["proposal_b_score"]) for r in ratings]
    p_val, eff_size = perform_statistical_test(group_a, group_b)
    assert isinstance(p_val, float)
    assert isinstance(eff_size, float)

def test_validity_metrics_written(tmp_path):
    # This test assumes the main workflow is run, which writes the file.
    # For unit testing, we verify the calculation function.
    scores_a = [5.0, 5.0, 5.0]
    scores_b = [4.0, 4.0, 4.0]
    metrics = calculate_validity_improvement(scores_a, scores_b)
    assert "mean_diff" in metrics
    assert "p_value" in metrics
    assert "effect_size" in metrics
    assert metrics["mean_diff"] == 1.0