import os
import json
import pytest
import tempfile
from pathlib import Path
import numpy as np

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.aggregate_static_results import (
    load_eval_scores,
    aggregate_metrics,
    save_aggregated_results
)

@pytest.fixture
def sample_scores():
    """Create sample per-document scores for testing."""
    return [
        {"document_id": "doc1", "perplexity": 10.5, "exact_match": 0.85},
        {"document_id": "doc2", "perplexity": 12.0, "exact_match": 0.90},
        {"document_id": "doc3", "perplexity": 11.5, "exact_match": 0.88},
        {"document_id": "doc4", "perplexity": 13.0, "exact_match": 0.92},
        {"document_id": "doc5", "perplexity": 11.0, "exact_match": 0.87}
    ]

@pytest.fixture
def temp_input_file(sample_scores):
    """Create a temporary JSON file with sample scores."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_scores, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_output_file():
    """Create a temporary output file path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    os.unlink(temp_path)  # Remove the empty file, we just need the path
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_load_eval_scores_valid(temp_input_file, sample_scores):
    """Test loading valid JSON scores."""
    scores = load_eval_scores(temp_input_file)
    assert len(scores) == len(sample_scores)
    assert scores[0]["document_id"] == "doc1"
    assert "perplexity" in scores[0]

def test_load_eval_scores_missing_file():
    """Test loading from a non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_eval_scores("/nonexistent/path/file.json")

def test_load_eval_scores_invalid_format(temp_input_file):
    """Test loading non-list JSON raises ValueError."""
    with open(temp_input_file, 'w') as f:
        json.dump({"not": "a list"}, f)
    
    with pytest.raises(ValueError):
        load_eval_scores(temp_input_file)

def test_aggregate_metrics_perplexity(sample_scores):
    """Test aggregation of perplexity metric."""
    result = aggregate_metrics(sample_scores, metric_name="perplexity")
    
    # Expected values
    values = [s["perplexity"] for s in sample_scores]
    expected_mean = np.mean(values)
    expected_std = np.std(values)
    expected_var = np.var(values)
    
    assert abs(result["mean_metric"] - expected_mean) < 1e-6
    assert abs(result["std_metric"] - expected_std) < 1e-6
    assert abs(result["variance_metric"] - expected_var) < 1e-6
    assert result["n_documents"] == len(sample_scores)
    assert result["metric_name"] == "perplexity"

def test_aggregate_metrics_exact_match(sample_scores):
    """Test aggregation of exact_match metric."""
    result = aggregate_metrics(sample_scores, metric_name="exact_match")
    
    values = [s["exact_match"] for s in sample_scores]
    expected_mean = np.mean(values)
    expected_std = np.std(values)
    
    assert abs(result["mean_metric"] - expected_mean) < 1e-6
    assert abs(result["std_metric"] - expected_std) < 1e-6
    assert result["n_documents"] == len(sample_scores)

def test_aggregate_metrics_empty_list():
    """Test aggregation with empty list raises ValueError."""
    with pytest.raises(ValueError):
        aggregate_metrics([], metric_name="perplexity")

def test_aggregate_metrics_missing_metric(sample_scores):
    """Test aggregation when metric is missing from some documents."""
    # Remove perplexity from one document
    modified_scores = [
        {"document_id": "doc1", "exact_match": 0.85},  # No perplexity
        {"document_id": "doc2", "perplexity": 12.0, "exact_match": 0.90}
    ]
    
    # Should skip the document without perplexity
    result = aggregate_metrics(modified_scores, metric_name="perplexity")
    assert result["n_documents"] == 1
    assert result["mean_metric"] == 12.0

def test_save_aggregated_results(temp_output_file, sample_scores):
    """Test saving aggregated results to JSON."""
    agg_data = aggregate_metrics(sample_scores, metric_name="perplexity")
    save_aggregated_results(agg_data, temp_output_file)
    
    assert os.path.exists(temp_output_file)
    
    with open(temp_output_file, 'r') as f:
        saved_data = json.load(f)
    
    assert "mean_metric" in saved_data
    assert "std_metric" in saved_data
    assert saved_data["mean_metric"] == agg_data["mean_metric"]

def test_aggregation_matches_manual_calculation(sample_scores):
    """Verify aggregation logic matches manual calculation on small subset."""
    # Use first 3 documents for manual calculation
    subset = sample_scores[:3]
    perplexities = [s["perplexity"] for s in subset]
    
    manual_mean = sum(perplexities) / len(perplexities)
    manual_var = sum((x - manual_mean) ** 2 for x in perplexities) / len(perplexities)
    manual_std = manual_var ** 0.5
    
    result = aggregate_metrics(subset, metric_name="perplexity")
    
    assert abs(result["mean_metric"] - manual_mean) < 1e-6
    assert abs(result["std_metric"] - manual_std) < 1e-6
    assert abs(result["variance_metric"] - manual_var) < 1e-6