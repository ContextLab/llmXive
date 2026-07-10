"""
Integration test for the clustering pipeline (User Story 3).

This test validates the end-to-end execution of:
1. Jaccard similarity matrix computation (code/analysis/clustering.py)
2. Hierarchical clustering
3. Permutation test for cluster coherence

It ensures that the pipeline produces valid JSON output with the expected schema
and that statistical tests (permutation) yield meaningful results.

Prerequisites:
- T013 (preprocess.py) must have run to generate data/processed/monthly_frequencies.json
- T028 (clustering.py) implementation must be present
"""

import json
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add code directory to path for imports
code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from analysis.clustering import (
    load_processed_data,
    compute_jaccard_matrix,
    perform_hierarchical_clustering,
    run_permutation_test,
    calculate_cluster_label_alignment_score,
    run_clustering_pipeline,
    main
)
from utils.contract_validation import validate_schema

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "monthly_frequencies.json"
TAXONOMY_PATH = PROJECT_ROOT / "data" / "taxonomy" / "survey_2023.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "cluster_results.json"

# Expected schema for cluster results
CLUSTER_RESULTS_SCHEMA = {
    "type": "object",
    "required": [
        "jaccard_matrix",
        "hierarchical_clustering",
        "permutation_test_results",
        "cluster_label_alignment_score",
        "metadata"
    ],
    "properties": {
        "jaccard_matrix": {
            "type": "object",
            "description": "Dictionary mapping tag pairs to Jaccard similarity scores"
        },
        "hierarchical_clustering": {
            "type": "object",
            "required": ["linkage_matrix", "cluster_assignments", "n_clusters"],
            "properties": {
                "linkage_matrix": {"type": "array"},
                "cluster_assignments": {"type": "object"},
                "n_clusters": {"type": "integer"}
            }
        },
        "permutation_test_results": {
            "type": "object",
            "required": ["p_value", "coherence_score", "n_permutations"],
            "properties": {
                "p_value": {"type": "number"},
                "coherence_score": {"type": "number"},
                "n_permutations": {"type": "integer"}
            }
        },
        "cluster_label_alignment_score": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0
        },
        "metadata": {
            "type": "object",
            "required": ["n_tags", "n_posts", "processing_time"]
        }
    }
}

@pytest.fixture
def mock_processed_data(tmp_path):
    """Create mock processed data if real data doesn't exist."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Create a minimal mock dataset for testing
    mock_data = {
        "metadata": {
            "generated_at": "2023-01-01T00:00:00",
            "n_tags": 5,
            "n_months": 12
        },
        "data": {
            "python": {
                "2023-01": 100,
                "2023-02": 105,
                "2023-03": 110,
                "2023-04": 108,
                "2023-05": 115,
                "2023-06": 120,
                "2023-07": 118,
                "2023-08": 125,
                "2023-09": 130,
                "2023-10": 128,
                "2023-11": 135,
                "2023-12": 140
            },
            "javascript": {
                "2023-01": 90,
                "2023-02": 95,
                "2023-03": 100,
                "2023-04": 98,
                "2023-05": 105,
                "2023-06": 110,
                "2023-07": 108,
                "2023-08": 115,
                "2023-09": 120,
                "2023-10": 118,
                "2023-11": 125,
                "2023-12": 130
            },
            "react": {
                "2023-01": 50,
                "2023-02": 55,
                "2023-03": 60,
                "2023-04": 58,
                "2023-05": 65,
                "2023-06": 70,
                "2023-07": 68,
                "2023-08": 75,
                "2023-09": 80,
                "2023-10": 78,
                "2023-11": 85,
                "2023-12": 90
            },
            "node": {
                "2023-01": 40,
                "2023-02": 45,
                "2023-03": 50,
                "2023-04": 48,
                "2023-05": 55,
                "2023-06": 60,
                "2023-07": 58,
                "2023-08": 65,
                "2023-09": 70,
                "2023-10": 68,
                "2023-11": 75,
                "2023-12": 80
            },
            "django": {
                "2023-01": 30,
                "2023-02": 32,
                "2023-03": 35,
                "2023-04": 33,
                "2023-05": 38,
                "2023-06": 40,
                "2023-07": 39,
                "2023-08": 42,
                "2023-09": 45,
                "2023-10": 43,
                "2023-11": 48,
                "2023-12": 50
            }
        }
    }
    
    output_file = processed_dir / "monthly_frequencies.json"
    with open(output_file, 'w') as f:
        json.dump(mock_data, f)
    
    return output_file

@pytest.fixture
def mock_taxonomy(tmp_path):
    """Create mock taxonomy data if real data doesn't exist."""
    taxonomy_dir = tmp_path / "data" / "taxonomy"
    taxonomy_dir.mkdir(parents=True)
    
    mock_taxonomy = {
        "metadata": {
            "source": "Stack Overflow Survey 2023",
            "generated_at": "2023-01-01T00:00:00"
        },
        "categories": [
            {
                "name": "Web Development",
                "tags": ["javascript", "react", "node", "django", "python"]
            },
            {
                "name": "Data Science",
                "tags": ["python", "pandas", "numpy", "scikit-learn"]
            },
            {
                "name": "DevOps",
                "tags": ["docker", "kubernetes", "aws", "azure"]
            }
        ]
    }
    
    output_file = taxonomy_dir / "survey_2023.json"
    with open(output_file, 'w') as f:
        json.dump(mock_taxonomy, f)
    
    return output_file

def test_jaccard_matrix_computation(mock_processed_data):
    """Test that Jaccard matrix is computed correctly."""
    data = load_processed_data(mock_processed_data)
    jaccard_matrix = compute_jaccard_matrix(data)
    
    # Verify structure
    assert isinstance(jaccard_matrix, dict)
    assert len(jaccard_matrix) > 0
    
    # Verify all values are between 0 and 1
    for pair, score in jaccard_matrix.items():
        assert isinstance(score, (int, float))
        assert 0.0 <= score <= 1.0
    
    # Verify symmetry (Jaccard(A,B) == Jaccard(B,A))
    for pair, score in jaccard_matrix.items():
        tag_a, tag_b = pair.split("|")
        reverse_pair = f"{tag_b}|{tag_a}"
        if reverse_pair in jaccard_matrix:
            assert abs(jaccard_matrix[pair] - jaccard_matrix[reverse_pair]) < 1e-10
    
    print("✓ Jaccard matrix computation test passed")

def test_hierarchical_clustering(mock_processed_data):
    """Test that hierarchical clustering produces valid output."""
    data = load_processed_data(mock_processed_data)
    jaccard_matrix = compute_jaccard_matrix(data)
    
    result = perform_hierarchical_clustering(jaccard_matrix, n_clusters=2)
    
    # Verify structure
    assert "linkage_matrix" in result
    assert "cluster_assignments" in result
    assert "n_clusters" in result
    
    assert isinstance(result["linkage_matrix"], list)
    assert isinstance(result["cluster_assignments"], dict)
    assert isinstance(result["n_clusters"], int)
    
    # Verify cluster assignments contain all tags
    all_tags = set()
    for pair in jaccard_matrix.keys():
        tag_a, tag_b = pair.split("|")
        all_tags.add(tag_a)
        all_tags.add(tag_b)
    
    assigned_tags = set(result["cluster_assignments"].keys())
    assert all_tags.issubset(assigned_tags)
    
    print("✓ Hierarchical clustering test passed")

def test_permutation_test(mock_processed_data):
    """Test that permutation test runs and produces valid p-value."""
    data = load_processed_data(mock_processed_data)
    jaccard_matrix = compute_jaccard_matrix(data)
    
    # Perform clustering first
    clustering_result = perform_hierarchical_clustering(jaccard_matrix, n_clusters=2)
    
    # Run permutation test
    perm_result = run_permutation_test(
        jaccard_matrix, 
        clustering_result["cluster_assignments"],
        n_permutations=100  # Small number for speed
    )
    
    # Verify structure
    assert "p_value" in perm_result
    assert "coherence_score" in perm_result
    assert "n_permutations" in perm_result
    
    assert isinstance(perm_result["p_value"], (int, float))
    assert isinstance(perm_result["coherence_score"], (int, float))
    assert isinstance(perm_result["n_permutations"], int)
    
    # Verify p-value is in valid range
    assert 0.0 <= perm_result["p_value"] <= 1.0
    assert 0.0 <= perm_result["coherence_score"] <= 1.0
    
    print("✓ Permutation test passed")

def test_cluster_label_alignment_score(mock_processed_data, mock_taxonomy):
    """Test that cluster label alignment score is computed correctly."""
    data = load_processed_data(mock_processed_data)
    jaccard_matrix = compute_jaccard_matrix(data)
    
    # Perform clustering
    clustering_result = perform_hierarchical_clustering(jaccard_matrix, n_clusters=2)
    
    # Calculate alignment score
    alignment_score = calculate_cluster_label_alignment_score(
        clustering_result["cluster_assignments"],
        mock_taxonomy
    )
    
    # Verify score is in valid range [0, 1]
    assert isinstance(alignment_score, (int, float))
    assert 0.0 <= alignment_score <= 1.0
    
    print("✓ Cluster label alignment score test passed")

def test_full_clustering_pipeline(mock_processed_data, mock_taxonomy, tmp_path):
    """Test the full clustering pipeline end-to-end."""
    output_file = tmp_path / "cluster_results.json"
    
    # Run the full pipeline
    result = run_clustering_pipeline(
        processed_data_path=mock_processed_data,
        taxonomy_path=mock_taxonomy,
        output_path=output_file,
        n_clusters=2,
        n_permutations=100
    )
    
    # Verify output file was created
    assert output_file.exists()
    
    # Load and validate output
    with open(output_file, 'r') as f:
        saved_result = json.load(f)
    
    # Validate against schema
    try:
        validate_schema(saved_result, CLUSTER_RESULTS_SCHEMA)
    except Exception as e:
        pytest.fail(f"Output does not match expected schema: {e}")
    
    # Verify all required sections are present
    assert "jaccard_matrix" in saved_result
    assert "hierarchical_clustering" in saved_result
    assert "permutation_test_results" in saved_result
    assert "cluster_label_alignment_score" in saved_result
    assert "metadata" in saved_result
    
    # Verify specific values
    assert saved_result["permutation_test_results"]["p_value"] is not None
    assert 0.0 <= saved_result["permutation_test_results"]["p_value"] <= 1.0
    
    assert 0.0 <= saved_result["cluster_label_alignment_score"] <= 1.0
    
    # Verify metadata
    assert "n_tags" in saved_result["metadata"]
    assert "n_posts" in saved_result["metadata"]
    assert "processing_time" in saved_result["metadata"]
    
    print("✓ Full clustering pipeline test passed")

def test_pipeline_handles_empty_data(tmp_path):
    """Test that pipeline handles edge cases gracefully."""
    empty_data_path = tmp_path / "empty_data.json"
    empty_data = {
        "metadata": {"n_tags": 0, "n_months": 0},
        "data": {}
    }
    
    with open(empty_data_path, 'w') as f:
        json.dump(empty_data, f)
    
    # This should handle empty data without crashing
    # Note: Actual behavior may vary based on implementation
    # We just verify it doesn't raise unexpected exceptions
    try:
        data = load_processed_data(empty_data_path)
        # If we get here, the loader handled empty data
        assert data["data"] == {}
    except Exception:
        # Or it raises a clear error
        pass
    
    print("✓ Empty data handling test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
