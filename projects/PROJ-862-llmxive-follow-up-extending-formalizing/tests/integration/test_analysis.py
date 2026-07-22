"""
Integration test for the end-to-end analysis pipeline (Task T028).

This test verifies that the analysis pipeline (T029, T030, T031) correctly:
1. Loads baseline and perturbed vectors from CSV files.
2. Filters pairs based on validity logs (Input Drift & Output Validity).
3. Calculates pairwise cosine similarities.
4. Runs the appropriate hypothesis test (t-test or Wilcoxon).
5. Generates a sensitivity report and statistical results JSON.

It uses a small, deterministic synthetic dataset generation ONLY for the purpose
of verifying the pipeline logic (loading, filtering, calculation, test selection)
without requiring a full re-run of the heavy perturbation sweep. The data is
generated to mimic the expected schema and constraints of the real data.
"""
import os
import json
import csv
import tempfile
import shutil
import numpy as np
import torch
import pytest
from pathlib import Path

# Import pipeline components
from code.analysis import (
    calculate_pairwise_cosine_similarity,
    run_hypothesis_test,
    generate_sensitivity_report,
    run_full_analysis
)
from code.config import load_config, PipelineConfig
from code.validity_check import check_validity_collapse

# Constants for test data generation
TEST_HIDDEN_SIZE = 768
TEST_NUM_PAIRS = 50
TEST_SIGMA = 0.1
TEST_TASK_TYPE = "math_reasoning"


def _generate_mock_vectors(num_pairs, hidden_size, seed=42):
    """Generate deterministic mock vectors for testing."""
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    # Generate baseline vectors (unit normalized)
    baseline_vectors = np.random.randn(num_pairs, hidden_size).astype(np.float32)
    baseline_vectors = baseline_vectors / np.linalg.norm(baseline_vectors, axis=1, keepdims=True)
    
    # Generate perturbed vectors (slightly shifted to ensure difference)
    perturbed_vectors = baseline_vectors + 0.05 * np.random.randn(num_pairs, hidden_size).astype(np.float32)
    perturbed_vectors = perturbed_vectors / np.linalg.norm(perturbed_vectors, axis=1, keepdims=True)
    
    return baseline_vectors, perturbed_vectors


def _create_mock_data_files(tmp_dir, num_pairs, hidden_size, task_type, sigma):
    """Create mock CSV files mimicking the real pipeline output."""
    base_path = Path(tmp_dir)
    
    # 1. Create pairing config
    pairing_data = []
    for i in range(num_pairs):
        pairing_data.append({
            "pair_id": f"pair_{i:04d}",
            "task_type": task_type,
            "question_a": f"Question A {i}",
            "question_b": f"Question B {i}",
            "expected_answer": f"Answer {i}"
        })
    
    pairing_file = base_path / "pairing_config.json"
    with open(pairing_file, 'w') as f:
        json.dump(pairing_data, f)
    
    # 2. Create baseline vectors CSV
    baseline_vectors, perturbed_vectors = _generate_mock_vectors(num_pairs, hidden_size)
    
    baseline_csv = base_path / "baseline_vectors.csv"
    with open(baseline_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["pair_id", "task_type", "vector"])
        for i, (pair, vec) in enumerate(zip(pairing_data, baseline_vectors)):
            vec_str = ",".join(map(str, vec))
            writer.writerow([pair["pair_id"], pair["task_type"], f"[{vec_str}]"])
    
    # 3. Create perturbed vectors CSV
    perturbed_csv = base_path / "perturbed_vectors.csv"
    with open(perturbed_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["pair_id", "task_type", "sigma", "vector"])
        for i, (pair, vec) in enumerate(zip(pairing_data, perturbed_vectors)):
            vec_str = ",".join(map(str, vec))
            writer.writerow([pair["pair_id"], pair["task_type"], sigma, f"[{vec_str}]"])
    
    # 4. Create validity log (all passed for this test)
    validity_log_csv = base_path / "validity_log.csv"
    with open(validity_log_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["pair_id", "input_drift_passed", "output_validity_passed", "collapsed"])
        for i in range(num_pairs):
            writer.writerow([f"pair_{i:04d}", "True", "True", "False"])
    
    return pairing_file, baseline_csv, perturbed_csv, validity_log_csv


class TestAnalysisPipeline:
    """Integration tests for the analysis pipeline."""

    def setup_method(self):
        """Set up temporary directory for test artifacts."""
        self.tmp_dir = tempfile.mkdtemp()
        self.test_task_type = TEST_TASK_TYPE
        self.test_sigma = TEST_SIGMA

    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_pairwise_cosine_similarity_calculation(self):
        """Test that pairwise cosine similarity is calculated correctly."""
        # Arrange
        baseline_vectors, perturbed_vectors = _generate_mock_vectors(TEST_NUM_PAIRS, TEST_HIDDEN_SIZE)
        pair_ids = [f"pair_{i:04d}" for i in range(TEST_NUM_PAIRS)]
        
        # Act
        baseline_sims, perturbed_sims = calculate_pairwise_cosine_similarity(
            (baseline_vectors, pair_ids), 
            (perturbed_vectors, pair_ids)
        )
        
        # Assert
        assert len(baseline_sims) == TEST_NUM_PAIRS
        assert len(perturbed_sims) == TEST_NUM_PAIRS
        assert all(-1.0 <= s <= 1.0 for s in baseline_sims)
        assert all(-1.0 <= s <= 1.0 for s in perturbed_sims)
        # Verify perturbed sims are generally lower (more separated) due to noise
        assert np.mean(perturbed_sims) < np.mean(baseline_sims)

    def test_hypothesis_test_selection(self):
        """Test that the correct statistical test is selected based on normality."""
        # Arrange
        baseline_vectors, perturbed_vectors = _generate_mock_vectors(TEST_NUM_PAIRS, TEST_HIDDEN_SIZE)
        pair_ids = [f"pair_{i:04d}" for i in range(TEST_NUM_PAIRS)]
        
        baseline_sims, perturbed_sims = calculate_pairwise_cosine_similarity(
            (baseline_vectors, pair_ids),
            (perturbed_vectors, pair_ids)
        )
        
        # Act
        result = run_hypothesis_test(baseline_sims, perturbed_sims)
        
        # Assert
        assert "test_name" in result
        assert "p_value" in result
        assert "statistic" in result
        assert "significant" in result
        assert result["test_name"] in ["paired_t_test", "wilcoxon_signed_rank"]

    def test_full_integration_pipeline(self):
        """Test the full end-to-end analysis pipeline with mock data."""
        # Arrange
        (pairing_file, baseline_csv, perturbed_csv, validity_log_csv) = _create_mock_data_files(
            self.tmp_dir, TEST_NUM_PAIRS, TEST_HIDDEN_SIZE, self.test_task_type, self.test_sigma
        )
        
        # Create a mock config for the analysis
        config = PipelineConfig(
            data_dir=self.tmp_dir,
            output_dir=self.tmp_dir,
            task_type=self.test_task_type,
            sigma_values=[self.test_sigma],
            memory_limit_mb=7000
        )
        
        # Act
        results = run_full_analysis(
            config=config,
            baseline_csv_path=baseline_csv,
            perturbed_csv_path=perturbed_csv,
            validity_log_path=validity_log_csv
        )
        
        # Assert
        assert results is not None
        assert "statistical_results" in results
        assert "sensitivity_report" in results
        
        stat_res = results["statistical_results"]
        assert "test_name" in stat_res
        assert "p_value" in stat_res
        assert "significant" in stat_res
        
        # Verify output files were created
        assert os.path.exists(os.path.join(self.tmp_dir, "statistical_results.json"))
        assert os.path.exists(os.path.join(self.tmp_dir, "sensitivity_report.json"))

    def test_validity_filtering(self):
        """Test that invalid pairs are correctly filtered out."""
        # Arrange
        # Create mock data where 50% of pairs are invalid
        num_valid = TEST_NUM_PAIRS // 2
        num_invalid = TEST_NUM_PAIRS - num_valid
        
        # Create validity log with some failures
        validity_log_csv = Path(self.tmp_dir) / "validity_log.csv"
        with open(validity_log_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["pair_id", "input_drift_passed", "output_validity_passed", "collapsed"])
            for i in range(num_valid):
                writer.writerow([f"pair_{i:04d}", "True", "True", "False"])
            for i in range(num_valid, TEST_NUM_PAIRS):
                writer.writerow([f"pair_{i:04d}", "False", "True", "False"]) # Failed input drift
        
        # Create mock vectors
        baseline_vectors, perturbed_vectors = _generate_mock_vectors(TEST_NUM_PAIRS, TEST_HIDDEN_SIZE)
        
        baseline_csv = Path(self.tmp_dir) / "baseline_vectors.csv"
        with open(baseline_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["pair_id", "task_type", "vector"])
            for i, vec in enumerate(baseline_vectors):
                vec_str = ",".join(map(str, vec))
                writer.writerow([f"pair_{i:04d}", self.test_task_type, f"[{vec_str}]"])
        
        perturbed_csv = Path(self.tmp_dir) / "perturbed_vectors.csv"
        with open(perturbed_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["pair_id", "task_type", "sigma", "vector"])
            for i, vec in enumerate(perturbed_vectors):
                vec_str = ",".join(map(str, vec))
                writer.writerow([f"pair_{i:04d}", self.test_task_type, self.test_sigma, f"[{vec_str}]"])
        
        # Act
        # Manually invoke the filtering logic from run_full_analysis
        from code.analysis import load_and_filter_vectors
        baseline_filtered, perturbed_filtered = load_and_filter_vectors(
            baseline_csv, perturbed_csv, validity_log_csv, self.test_task_type, self.test_sigma
        )
        
        # Assert
        # Should only have the valid pairs
        assert len(baseline_filtered) == num_valid
        assert len(perturbed_filtered) == num_valid
        
        # Verify IDs are correct
        expected_ids = [f"pair_{i:04d}" for i in range(num_valid)]
        actual_ids = [p["pair_id"] for p in baseline_filtered]
        assert actual_ids == expected_ids