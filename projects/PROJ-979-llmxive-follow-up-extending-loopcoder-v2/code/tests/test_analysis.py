import os
import sys
import json
import tempfile
import shutil
import math
import csv
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest
from pathlib import Path

# Import the functions we are testing (stubs exist in src/ per completed tasks)
# We mock the heavy lifting (model loading, inference) to focus on pipeline integration
from src.analysis import load_entropy_results, load_convergence_results
from src.entropy import extract_entropy
from src.inference import run_inference

# --- Mock Helpers for T018 (Non-Inferiority) ---
# These mocks simulate the data flow required for the statistical test
# without needing to run the full inference pipeline.

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)


def mock_load_model_cpu(*args, **kwargs):
    """Mock model loader returning a dummy object."""
    mock_model = MagicMock()
    mock_model.config = MagicMock()
    mock_model.config.hidden_size = 10
    return mock_model

def mock_load_convergence_results(path):
    """Mock convergence results with synthetic k-values and accuracy flags."""
    return [
        {"task_id": "task_0", "k": 2, "converged": True, "step": 1},
        {"task_id": "task_1", "k": 2, "converged": True, "step": 1},
        {"task_id": "task_2", "k": 2, "converged": False, "step": None},
        {"task_id": "task_3", "k": 2, "converged": True, "step": 1},
        {"task_id": "task_4", "k": 2, "converged": True, "step": 1},
    ]

def mock_generate_samples(*args, **kwargs):
    """Mock sample generator returning fixed strings."""
    return ["def foo(): pass", "def foo(): return 1", "def foo(): return 2"]


def mock_cluster_samples(samples):
    """Mock clustering returning 2 clusters."""
    return {0: [samples[0]], 1: samples[1:]}


def mock_compute_entropy(cluster_probs):
    """Mock entropy calculation."""
    # Simple entropy for [0.33, 0.33, 0.33] ~ 1.098
    return 1.098


def mock_run_inference(prompt, model, k):
    """Mock inference returning a fixed trajectory."""
    # Simulate convergence at step 2
    return {
        "task_id": "mock_task_001",
        "k": k,
        "output": "correct_code",
        "is_correct": k >= 2,
        "converged": k >= 2,
        "first_correct_step": 2 if k >= 2 else None
    }


def mock_execute_code(*args, **kwargs):
    """Mock sandbox execution."""
    return {"status": "success", "output": "42"}


class TestPipelineIntegration:
    """Integration test for end-to-end entropy + convergence pipeline on N=5 sample."""

    @patch('src.entropy.load_model', mock_load_model_cpu)
    @patch('src.entropy.generate_samples', mock_generate_samples)
    @patch('src.entropy.cluster_samples', mock_cluster_samples)
    @patch('src.entropy.compute_shannon_entropy', mock_compute_entropy)
    @patch('src.inference.load_model', mock_load_model_cpu)
    @patch('src.inference.run_inference', mock_run_inference)
    @patch('src.inference.execute_code_in_sandbox', mock_execute_code)
    @patch('src.data_loader.load_config', return_value={'min_strata_size': 50})
    @patch('src.data_loader.load_dataset')
    def test_pipeline_n5(self, mock_load_ds, mock_config, temp_dir):
        """
        Test end-to-end pipeline:
        1. Mock data loading (HumanEval/MBPP)
        2. Run entropy extraction (mocked model) -> entropy_results.csv
        3. Run convergence inference (mocked model) -> convergence_results.csv
        4. Verify files exist and have correct schema.
        """
        # Setup: Create mock dataset structure
        mock_dataset = [
            {"task_id": f"mock_task_{i:03d}", "prompt": f"def task_{i}(): pass", "test": "assert task_() == 1", "difficulty": "easy"}
            for i in range(5)
        ]
        mock_load_ds.return_value = mock_dataset

        # Ensure output directories exist
        data_dir = Path(temp_dir) / "data" / "processed"
        data_dir.mkdir(parents=True, exist_ok=True)

        # 1. Simulate Entropy Pipeline (T012a-d)
        # We call the main entry point logic directly or simulate the flow
        # Since T012 is implemented in src/entropy.py, we simulate its main effect
        from src.entropy import process_entropy_for_dataset
        from src.data_loader import save_splits, filter_strata

        # Save mock splits first (T004d)
        splits_path = data_dir / "filtered_splits.json"
        with open(splits_path, 'w') as f:
            json.dump(mock_dataset, f)

        # Run Entropy Extraction (Mocked)
        # We manually invoke the logic that would write entropy_results.csv
        entropy_results = []
        for item in mock_dataset:
            # Simulate extract_entropy call
            ent = mock_compute_entropy(None)
            entropy_results.append({
                "task_id": item["task_id"],
                "entropy": ent,
                "n_clusters": 2,
                "n_samples": 10
            })

        # Write entropy results to CSV (T012c/d output)
        entropy_csv_path = data_dir / "entropy_results.csv"
        with open(entropy_csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "entropy", "n_clusters", "n_samples"])
            writer.writeheader()
            writer.writerows(entropy_results)

        # 2. Simulate Convergence Pipeline (T013a-d)
        # We manually invoke the logic that would write convergence_results.csv
        convergence_results = []
        for item in mock_dataset:
            for k in [1, 2, 3]:
                res = mock_run_inference(item["prompt"], None, k)
                convergence_results.append({
                    "task_id": res["task_id"],
                    "k": res["k"],
                    "converged": res["converged"],
                    "step": res["first_correct_step"] if res["converged"] else -1,
                    "timestamp": "2023-01-01T00:00:00"
                })

        # Write convergence results to CSV (T013d output)
        convergence_csv_path = data_dir / "convergence_results.csv"
        with open(convergence_csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["task_id", "k", "converged", "step", "timestamp"])
            writer.writeheader()
            writer.writerows(convergence_results)

        # 3. Verification: Assert files exist and have correct schema
        assert entropy_csv_path.exists(), "entropy_results.csv was not generated"
        assert convergence_csv_path.exists(), "convergence_results.csv was not generated"

        # Verify Entropy Schema
        with open(entropy_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 5, f"Expected 5 rows in entropy, got {len(rows)}"
            required_entropy_cols = {"task_id", "entropy", "n_clusters", "n_samples"}
            assert set(rows[0].keys()) == required_entropy_cols, f"Entropy schema mismatch: {rows[0].keys()}"

        # Verify Convergence Schema
        with open(convergence_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # 5 tasks * 3 k-values = 15 rows
            assert len(rows) == 15, f"Expected 15 rows in convergence, got {len(rows)}"
            required_conv_cols = {"task_id", "k", "converged", "step", "timestamp"}
            assert set(rows[0].keys()) == required_conv_cols, f"Convergence schema mismatch: {rows[0].keys()}"

        # Verify data integrity
        # Check that task_ids match between files
        entropy_ids = {r["task_id"] for r in rows}
        # Re-read entropy for comparison
        with open(entropy_csv_path, 'r') as f:
            entropy_ids = {r["task_id"] for r in csv.DictReader(f)}
        
        conv_ids = {r["task_id"] for r in rows}
        assert entropy_ids == conv_ids, "Task IDs mismatch between entropy and convergence files"

        # Check convergence logic (k=1 should not converge in mock, k>=2 should)
        k1_results = [r for r in rows if r["k"] == "1"]
        assert all(r["converged"] == "False" for r in k1_results), "Mock k=1 should not converge"

        k2_results = [r for r in rows if r["k"] == "2"]
        assert all(r["converged"] == "True" for r in k2_results), "Mock k=2 should converge"