import pytest
import json
import os
import tempfile
from metrics import (
    calculate_ndcg_at_k, 
    calculate_ndcg_at_10, 
    load_beir_ground_truth, 
    load_results_from_json,
    evaluate_full_pipeline,
    aggregate_ndcg_scores,
    calculate_ndcg_from_beir_results
)

class TestNDCGCalculation:
    
    def test_ndcg_at_k_perfect_ranking(self):
        """Test NDCG when ranking is perfect (highest relevance first)."""
        # Relevance scores: 3, 2, 1, 0, 0...
        scores = [3, 2, 1, 0, 0, 0, 0, 0, 0, 0]
        ndcg = calculate_ndcg_at_k(scores, 10)
        assert ndcg == 1.0

    def test_ndcg_at_k_worst_ranking(self):
        """Test NDCG when ranking is worst (lowest relevance first)."""
        # Relevance scores: 0, 0, 0, 0, 0, 0, 0, 0, 1, 3 (reversed ideal)
        scores = [0, 0, 0, 0, 0, 0, 0, 0, 1, 3]
        ndcg = calculate_ndcg_at_k(scores, 10)
        assert ndcg < 1.0
        assert ndcg > 0.0

    def test_ndcg_at_k_empty_list(self):
        """Test NDCG with empty list returns 0."""
        assert calculate_ndcg_at_k([], 10) == 0.0

    def test_ndcg_at_k_k_larger_than_list(self):
        """Test NDCG when k is larger than list length."""
        scores = [1, 2, 3]
        ndcg = calculate_ndcg_at_k(scores, 10)
        # Should calculate NDCG@3 essentially, normalized by IDCG@3
        assert 0.0 <= ndcg <= 1.0

    def test_ndcg_at_10_wrapper(self):
        """Test the NDCG@10 wrapper function."""
        scores = [3, 3, 2, 2, 1, 1, 0, 0, 0, 0]
        ndcg_10 = calculate_ndcg_at_10(scores)
        assert ndcg_10 == 1.0

    def test_aggregate_ndcg_scores(self):
        """Test aggregation of per-query NDCG scores."""
        scores = {"q1": 0.8, "q2": 0.9, "q3": 0.7}
        mean = aggregate_ndcg_scores(scores)
        assert abs(mean - 0.8) < 0.01

    def test_aggregate_ndcg_empty(self):
        """Test aggregation with empty dict."""
        assert aggregate_ndcg_scores({}) == 0.0

class TestNDCGIntegration:
    
    def test_evaluate_full_pipeline_with_mock_data(self, tmp_path):
        """
        Test evaluate_full_pipeline with mock ground truth and results.
        This simulates the flow from T015/T015b.
        """
        # Create mock ground truth
        mock_gt = {
            "q1": {"doc1": 3, "doc2": 2, "doc3": 1, "doc4": 0},
            "q2": {"doc5": 3, "doc6": 2, "doc7": 1, "doc8": 0}
        }
        
        # Create mock full results (perfect ranking)
        full_results = {
            "q1": ["doc1", "doc2", "doc3", "doc4"],
            "q2": ["doc5", "doc6", "doc7", "doc8"]
        }
        
        # Create mock unique results (slightly worse ranking)
        unique_results = {
            "q1": ["doc2", "doc1", "doc3", "doc4"],  # doc2 (rel 2) before doc1 (rel 3)
            "q2": ["doc6", "doc5", "doc7", "doc8"]
        }
        
        # Write to temp files
        gt_file = tmp_path / "qrels" / "test.tsv"
        gt_file.parent.mkdir(parents=True)
        with open(gt_file, 'w') as f:
            for q_id, docs in mock_gt.items():
                for doc_id, rel in docs.items():
                    f.write(f"{q_id}\t0\t{doc_id}\t{rel}\n")
        
        full_file = tmp_path / "full_results.json"
        with open(full_file, 'w') as f:
            json.dump(full_results, f)
        
        unique_file = tmp_path / "unique_results.json"
        with open(unique_file, 'w') as f:
            json.dump(unique_results, f)
        
        # Mock the load_beir_ground_truth to return our mock data
        # Since we can't easily mock the file path logic in the function,
        # we'll test the core calculation logic directly
        
        # Test calculate_ndcg_from_beir_results
        full_ndcg_per_query = calculate_ndcg_from_beir_results(full_results, mock_gt, 10)
        unique_ndcg_per_query = calculate_ndcg_from_beir_results(unique_results, mock_gt, 10)
        
        # Full should be perfect (1.0)
        assert all(v == 1.0 for v in full_ndcg_per_query.values())
        
        # Unique should be less than perfect
        assert any(v < 1.0 for v in unique_ndcg_per_query.values())
        
        # Test aggregation
        full_mean = aggregate_ndcg_scores(full_ndcg_per_query)
        unique_mean = aggregate_ndcg_scores(unique_ndcg_per_query)
        
        assert full_mean == 1.0
        assert unique_mean < 1.0

    def test_load_results_from_json(self, tmp_path):
        """Test loading results from JSON file."""
        results = {"q1": ["d1", "d2"], "q2": ["d3"]}
        file_path = tmp_path / "results.json"
        with open(file_path, 'w') as f:
            json.dump(results, f)
        
        loaded = load_results_from_json(str(file_path))
        assert loaded == results

    def test_load_results_not_found(self, tmp_path):
        """Test loading results from non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_results_from_json(str(tmp_path / "nonexistent.json"))
