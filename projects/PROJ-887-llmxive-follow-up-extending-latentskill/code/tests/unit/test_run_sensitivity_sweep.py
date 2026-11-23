"""
Unit tests for src/evaluation/run_sensitivity_sweep.py
"""

import os
import sys
import tempfile
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.evaluation.run_sensitivity_sweep import run_sensitivity_sweep

class TestRunSensitivitySweep:
    def test_run_sensitivity_sweep_basic(self):
        """
        Test that the sensitivity sweep runs and produces valid output structure.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create dummy skill index
            skill_index_path = tmp_path / "skill_index.npz"
            vectors = np.random.rand(10, 100).astype(np.float32)
            np.savez(skill_index_path, vectors=vectors, in_features=10, out_features=10)
            
            # Create dummy query file
            query_path = tmp_path / "query_embeddings.npz"
            queries = np.random.rand(2, 100).astype(np.float32)
            metadata = np.array([{"task_id": "task1"}, {"task_id": "task2"}], dtype=object)
            np.savez(query_path, queries=queries, metadata=metadata)
            
            output_path = tmp_path / "sensitivity.yaml"
            
            # Mock the strategies imports to avoid heavy dependencies if needed,
            # but here we test the logic flow.
            # Since run_sensitivity_sweep imports from strategies, we need to ensure
            # the mocked functions return compatible shapes.
            
            with patch('src.evaluation.run_sensitivity_sweep.reconstruct_matrices') as mock_reconstruct:
                mock_reconstruct.return_value = (np.zeros((10, 10)), np.zeros((10, 10)))
                
                results = run_sensitivity_sweep(skill_index_path, query_path, output_path)
                
                assert "sweep_parameters" in results
                assert "results" in results
                assert len(results["results"]) == 4  # k in [1, 3, 5, 10]
                
                for res in results["results"]:
                    assert "k" in res
                    assert "query_results" in res
                    assert len(res["query_results"]) == 2  # 2 queries
                    
                    # Check that output file was created
                    assert output_path.exists()

    def test_run_sensitivity_sweep_empty_queries(self):
        """
        Test that the function handles empty query arrays gracefully (or raises).
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            skill_index_path = tmp_path / "skill_index.npz"
            vectors = np.random.rand(10, 100).astype(np.float32)
            np.savez(skill_index_path, vectors=vectors, in_features=10, out_features=10)
            
            query_path = tmp_path / "query_embeddings.npz"
            queries = np.random.rand(0, 100).astype(np.float32)
            metadata = np.array([], dtype=object)
            np.savez(query_path, queries=queries, metadata=metadata)
            
            output_path = tmp_path / "sensitivity.yaml"
            
            with patch('src.evaluation.run_sensitivity_sweep.reconstruct_matrices') as mock_reconstruct:
                mock_reconstruct.return_value = (np.zeros((10, 10)), np.zeros((10, 10)))
                
                # Should handle 0 queries without crashing, resulting in empty query_results
                results = run_sensitivity_sweep(skill_index_path, query_path, output_path)
                
                for res in results["results"]:
                    assert len(res["query_results"]) == 0
                    assert res["success_rate"] == 0.0

    def test_run_sensitivity_sweep_reconstruction_failure(self):
        """
        Test that failures in reconstruction are caught and logged.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            skill_index_path = tmp_path / "skill_index.npz"
            vectors = np.random.rand(10, 100).astype(np.float32)
            np.savez(skill_index_path, vectors=vectors, in_features=10, out_features=10)
            
            query_path = tmp_path / "query_embeddings.npz"
            queries = np.random.rand(1, 100).astype(np.float32)
            metadata = np.array([{"task_id": "task1"}], dtype=object)
            np.savez(query_path, queries=queries, metadata=metadata)
            
            output_path = tmp_path / "sensitivity.yaml"
            
            with patch('src.evaluation.run_sensitivity_sweep.reconstruct_matrices') as mock_reconstruct:
                mock_reconstruct.side_effect = ValueError("Invalid shape")
                
                results = run_sensitivity_sweep(skill_index_path, query_path, output_path)
                
                # Check that the result indicates failure
                k_res = results["results"][0] # k=1
                assert len(k_res["query_results"]) == 1
                assert k_res["query_results"][0]["success"] == False
                assert "error" in k_res["query_results"][0]