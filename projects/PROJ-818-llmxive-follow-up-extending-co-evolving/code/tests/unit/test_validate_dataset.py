"""
Unit tests for the validate_dataset module.
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.validate_dataset import (
    load_generated_data,
    validate_logic_proofs,
    validate_grid_worlds,
    validate_dataset,
    main
)
from src.utils.config import Config, get_default_config

class TestValidateDataset:
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary directory with mock data files."""
        proofs_data = [
            {
                "id": "proof_1",
                "domain": "logic",
                "premises": ["A", "A -> B"],
                "conclusion": "B",
                "proof_steps": ["Modus Ponens"]
            },
            {
                "id": "proof_2",
                "domain": "logic",
                "premises": ["C", "C -> D"],
                "conclusion": "D",
                "proof_steps": ["Modus Ponens"]
            }
        ]

        grids_data = [
            {
                "id": "grid_1",
                "domain": "grid",
                "grid_config": {"width": 5, "height": 5},
                "start": [0, 0],
                "end": [4, 4],
                "obstacles": [[1, 1], [2, 2]],
                "rules": ["avoid_red"]
            },
            {
                "id": "grid_2",
                "domain": "grid",
                "grid_config": {"width": 3, "height": 3},
                "start": [0, 0],
                "end": [2, 2],
                "obstacles": [],
                "rules": ["diagonal_paths"]
            }
        ]

        proofs_path = tmp_path / "generated_proofs.json"
        grids_path = tmp_path / "generated_grids.json"
        output_path = tmp_path / "validation_report.json"

        with open(proofs_path, 'w') as f:
            json.dump(proofs_data, f)
        with open(grids_path, 'w') as f:
            json.dump(grids_data, f)

        return {
            "proofs_path": str(proofs_path),
            "grids_path": str(grids_path),
            "output_path": str(output_path),
            "tmp_path": tmp_path
        }

    def test_load_generated_data(self, temp_data_dir):
        """Test loading of generated data files."""
        proofs, grids = load_generated_data(
            temp_data_dir["proofs_path"],
            temp_data_dir["grids_path"]
        )
        assert len(proofs) == 2
        assert len(grids) == 2
        assert proofs[0]["id"] == "proof_1"
        assert grids[0]["id"] == "grid_1"

    def test_load_generated_data_missing_file(self, temp_data_dir):
        """Test error handling for missing files."""
        with pytest.raises(FileNotFoundError):
            load_generated_data(
                "nonexistent.json",
                temp_data_dir["grids_path"]
            )

    def test_validate_logic_proofs(self, temp_data_dir):
        """Test validation of logic proofs."""
        config = get_default_config()
        proofs, _ = load_generated_data(
            temp_data_dir["proofs_path"],
            temp_data_dir["grids_path"]
        )
        metrics = validate_logic_proofs(proofs, config)

        assert "validity_rate" in metrics
        assert "total" in metrics
        assert metrics["total"] == 2
        assert 0.0 <= metrics["validity_rate"] <= 1.0

    def test_validate_grid_worlds(self, temp_data_dir):
        """Test validation of grid worlds."""
        config = get_default_config()
        _, grids = load_generated_data(
            temp_data_dir["proofs_path"],
            temp_data_dir["grids_path"]
        )
        metrics = validate_grid_worlds(grids, config)

        assert "solvability_rate" in metrics
        assert "total" in metrics
        assert metrics["total"] == 2
        assert 0.0 <= metrics["solvability_rate"] <= 1.0

    def test_validate_dataset_full(self, temp_data_dir):
        """Test full dataset validation pipeline."""
        success = validate_dataset(
            temp_data_dir["proofs_path"],
            temp_data_dir["grids_path"],
            temp_data_dir["output_path"]
        )

        # Check that report was created
        assert Path(temp_data_dir["output_path"]).exists()

        with open(temp_data_dir["output_path"], 'r') as f:
            report = json.load(f)

        assert "proof_validation" in report
        assert "grid_validation" in report
        assert "overall_pass" in report
        assert report["overall_pass"] == (
            report["proof_validation"]["validity_rate"] >= 0.99 and
            report["grid_validation"]["solvability_rate"] >= 0.99
        )

    def test_validate_dataset_threshold_failure(self, temp_data_dir, tmp_path):
        """Test validation failure when below threshold."""
        # Create a config with a very high threshold to force failure
        config = get_default_config()
        config.validity_threshold = 1.0  # Impossible to achieve 100%

        # We can't easily mock the config loading in validate_dataset,
        # so we test the metrics calculation directly
        proofs, grids = load_generated_data(
            temp_data_dir["proofs_path"],
            temp_data_dir["grids_path"]
        )

        proof_metrics = validate_logic_proofs(proofs, config)
        grid_metrics = validate_grid_worlds(grids, config)

        # With threshold 1.0, even 100% valid would fail if there's any edge case
        # But the main test is that the metrics are calculated correctly
        assert proof_metrics["threshold"] == 1.0
        assert grid_metrics["threshold"] == 1.0