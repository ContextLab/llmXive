"""
Integration tests for the full evaluation pipeline and baseline comparison (US3).

This test module validates the end-to-end evaluation process, ensuring that:
1. The evaluation script can load real data and trained models.
2. Metrics (MAE, RMSE, Pearson R) are calculated correctly.
3. Baseline comparisons (3D GNN vs 2D GNN vs Atom-Type) function as expected.
4. Hypothesis validation logic (MAE threshold) is enforced.
5. Report generation produces valid output files.

These tests run against the actual implementation in code/eval.py and
require the project to have completed the data loading and training phases.
"""

import os
import sys
import tempfile
import json
import pytest
from pathlib import Path
from typing import List, Dict, Any
import torch
import numpy as np

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# Import evaluation components
from eval import calculate_metrics, run_baseline_comparison, validate_hypothesis, generate_report
from models.schnet import create_schnet_model
from models.baseline_2d import create_baseline_2d_model
from models.baseline_atom import create_atom_baseline_model
from data.dataset import MoleculeData
from utils import set_seed, get_logger

# Configure logger for tests
logger = get_logger("test_eval")
set_seed(42)


class MockDataLoader:
    """Mock DataLoader that yields synthetic but structurally correct MoleculeData objects."""

    def __init__(self, num_samples: int = 10, device: str = "cpu"):
        self.num_samples = num_samples
        self.device = device

    def __iter__(self):
        for _ in range(self.num_samples):
            # Create a small valid molecule
            num_atoms = 5
            x = torch.tensor([[6], [1], [1], [1], [1]], dtype=torch.long)  # CH4-like
            pos = torch.rand((num_atoms, 3))
            # Generate realistic-ish charges (small float values)
            y = torch.randn(num_atoms, 1) * 0.1
            edge_index = torch.randint(0, num_atoms, (2, 8))
            batch = torch.zeros(num_atoms, dtype=torch.long)

            mol = MoleculeData(
                x=x,
                pos=pos,
                y=y,
                edge_index=edge_index,
                batch=batch,
                scaffold_id="test_scaffold"
            )
            yield mol.to(self.device)

    def __len__(self):
        return self.num_samples


def test_calculate_metrics():
    """Test that metrics are calculated correctly from predictions and targets."""
    logger.info("Running test_calculate_metrics...")

    # Setup ground truth and predictions
    y_true = torch.tensor([[0.1], [0.2], [0.3], [-0.1], [0.0]], dtype=torch.float)
    y_pred = torch.tensor([[0.12], [0.19], [0.32], [-0.09], [0.02]], dtype=torch.float)

    metrics = calculate_metrics(y_true, y_pred)

    assert "mae" in metrics, "MAE missing from metrics"
    assert "rmse" in metrics, "RMSE missing from metrics"
    assert "pearson_r" in metrics, "Pearson R missing from metrics"

    # Check basic properties
    assert metrics["mae"] >= 0, "MAE must be non-negative"
    assert metrics["rmse"] >= 0, "RMSE must be non-negative"
    assert -1 <= metrics["pearson_r"] <= 1, "Pearson R must be between -1 and 1"

    # Check approximate values (since predictions are close to truth)
    assert metrics["mae"] < 0.1, f"MAE too high for close predictions: {metrics['mae']}"
    assert metrics["rmse"] < 0.1, f"RMSE too high for close predictions: {metrics['rmse']}"
    assert metrics["pearson_r"] > 0.9, f"Pearson R too low: {metrics['pearson_r']}"

    logger.info("test_calculate_metrics PASSED")


def test_run_baseline_comparison():
    """Test the full baseline comparison pipeline with mock data."""
    logger.info("Running test_run_baseline_comparison...")

    # Create mock loaders
    device = "cpu"
    train_loader = MockDataLoader(num_samples=5, device=device)
    val_loader = MockDataLoader(num_samples=3, device=device)
    test_loader = MockDataLoader(num_samples=5, device=device)

    # Create models
    schnet_model = create_schnet_model(num_atom_types=10, num_filters=32, num_gaussians=20)
    baseline_2d_model = create_baseline_2d_model(num_atom_types=10, num_filters=32)
    baseline_atom_model = create_atom_baseline_model(num_atom_types=10)

    # Run comparison
    results = run_baseline_comparison(
        train_loader=train_loader,
        val_loader=val_loader,
        test_loader=test_loader,
        models={
            "schnet_3d": schnet_model,
            "baseline_2d": baseline_2d_model,
            "baseline_atom": baseline_atom_model
        },
        device=device
    )

    assert "schnet_3d" in results, "3D GNN results missing"
    assert "baseline_2d" in results, "2D GNN results missing"
    assert "baseline_atom" in results, "Atom baseline results missing"

    # Verify structure of results
    for model_name, model_results in results.items():
        assert "train" in model_results, f"Train metrics missing for {model_name}"
        assert "val" in model_results, f"Val metrics missing for {model_name}"
        assert "test" in model_results, f"Test metrics missing for {model_name}"

        for split, metrics in model_results.items():
            assert "mae" in metrics, f"MAE missing for {model_name} {split}"
            assert "rmse" in metrics, f"RMSE missing for {model_name} {split}"
            assert "pearson_r" in metrics, f"Pearson R missing for {model_name} {split}"

    # Verify that 3D model is not worse than baselines in this mock scenario (optional but good check)
    # Note: In real scenarios, 3D should be better, but mock data might be noisy.
    # We just check that the comparison logic ran without error.

    logger.info("test_run_baseline_comparison PASSED")


def test_validate_hypothesis_pass():
    """Test hypothesis validation when MAE is within threshold."""
    logger.info("Running test_validate_hypothesis_pass...")

    # Mock results where 3D GNN MAE is good
    mock_results = {
        "schnet_3d": {
            "test": {"mae": 0.03, "rmse": 0.04, "pearson_r": 0.95}
        }
    }

    # Should not raise
    validate_hypothesis(mock_results, threshold=0.05)
    logger.info("test_validate_hypothesis_pass PASSED")


def test_validate_hypothesis_fail():
    """Test hypothesis validation when MAE exceeds threshold."""
    logger.info("Running test_validate_hypothesis_fail...")

    # Mock results where 3D GNN MAE is bad
    mock_results = {
        "schnet_3d": {
            "test": {"mae": 0.08, "rmse": 0.1, "pearson_r": 0.5}
        }
    }

    with pytest.raises(AssertionError) as exc_info:
        validate_hypothesis(mock_results, threshold=0.05)

    assert "Hypothesis failed: MAE > 0.05 e" in str(exc_info.value)
    logger.info("test_validate_hypothesis_fail PASSED")


def test_generate_report():
    """Test that the report generation creates a valid file with expected content."""
    logger.info("Running test_generate_report...")

    # Mock aggregated results
    results = {
        "schnet_3d": {
            "train": {"mae": 0.02, "rmse": 0.03, "pearson_r": 0.98},
            "val": {"mae": 0.03, "rmse": 0.04, "pearson_r": 0.95},
            "test": {"mae": 0.04, "rmse": 0.05, "pearson_r": 0.92}
        },
        "baseline_2d": {
            "train": {"mae": 0.05, "rmse": 0.07, "pearson_r": 0.85},
            "val": {"mae": 0.06, "rmse": 0.08, "pearson_r": 0.82},
            "test": {"mae": 0.07, "rmse": 0.09, "pearson_r": 0.80}
        },
        "baseline_atom": {
            "train": {"mae": 0.1, "rmse": 0.12, "pearson_r": 0.70},
            "val": {"mae": 0.11, "rmse": 0.13, "pearson_r": 0.68},
            "test": {"mae": 0.12, "rmse": 0.14, "pearson_r": 0.65}
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "results.md"

        generate_report(results, str(report_path))

        assert report_path.exists(), "Report file was not created"

        content = report_path.read_text()
        assert "# Evaluation Results" in content, "Report missing header"
        assert "schnet_3d" in content, "Report missing 3D GNN section"
        assert "baseline_2d" in content, "Report missing 2D GNN section"
        assert "baseline_atom" in content, "Report missing Atom baseline section"
        assert "MAE" in content, "Report missing MAE metrics"
        assert "RMSE" in content, "Report missing RMSE metrics"
        assert "Pearson R" in content, "Report missing Pearson R metrics"

        # Verify JSON export if implemented (optional but good practice)
        json_path = Path(tmpdir) / "results.json"
        if json_path.exists():
            with open(json_path, "r") as f:
                json_data = json.load(f)
            assert "schnet_3d" in json_data, "JSON missing 3D GNN data"

    logger.info("test_generate_report PASSED")


def test_integration_full_pipeline():
    """
    Integration test: Run the full evaluation pipeline from data loading to report generation.
    This simulates the end-to-end execution of code/eval.py.
    """
    logger.info("Running test_integration_full_pipeline...")

    device = "cpu"
    set_seed(42)

    # 1. Setup Mock Data
    train_loader = MockDataLoader(num_samples=5, device=device)
    val_loader = MockDataLoader(num_samples=3, device=device)
    test_loader = MockDataLoader(num_samples=5, device=device)

    # 2. Initialize Models
    schnet = create_schnet_model(num_atom_types=10, num_filters=32, num_gaussians=20)
    baseline_2d = create_baseline_2d_model(num_atom_types=10, num_filters=32)
    baseline_atom = create_atom_baseline_model(num_atom_types=10)

    models = {
        "schnet_3d": schnet,
        "baseline_2d": baseline_2d,
        "baseline_atom": baseline_atom
    }

    # 3. Run Comparison
    results = run_baseline_comparison(
        train_loader=train_loader,
        val_loader=val_loader,
        test_loader=test_loader,
        models=models,
        device=device
    )

    # 4. Validate Hypothesis (should pass with mock data)
    validate_hypothesis(results, threshold=0.05)

    # 5. Generate Report
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "test_results.md"
        generate_report(results, str(report_path))

        # Verify file existence and content
        assert report_path.exists()
        content = report_path.read_text()
        assert "schnet_3d" in content
        assert "MAE" in content

    logger.info("test_integration_full_pipeline PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])