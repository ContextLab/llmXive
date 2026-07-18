"""
Tests for T013: Validation logic.
"""
import pytest
import tempfile
import json
from pathlib import Path
import torch

from src.data.validation import validate_unique_ids, MIN_UNIQUE_SUBJECTS
from src.utils.io import save_tensor, save_csv


class TestValidation:
    """Test suite for validation logic."""

    def test_validation_success(self, tmp_path):
        """Test validation passes when sufficient unique IDs exist."""
        # Setup
        embeddings_dir = tmp_path / "embeddings"
        embeddings_dir.mkdir()
        complexity_csv = tmp_path / "complexity.csv"
        failed_log = tmp_path / "failed.log"

        # Create 100 valid embedding files
        for i in range(100):
            save_tensor(torch.randn(1, 512), embeddings_dir / f"subject_{i}.pt")

        # Create matching CSV
        csv_data = [{"subject_id": f"subject_{i}", "complexity_score": 0.5} for i in range(100)]
        save_csv(csv_data, complexity_csv)

        # Run validation
        result = validate_unique_ids(embeddings_dir, complexity_csv, failed_log)

        # Assert
        assert result["success"] is True
        assert result["unique_subjects"] == 100
        assert result["min_required"] == MIN_UNIQUE_SUBJECTS
        assert result["failures_count"] == 0

    def test_validation_failure_insufficient_ids(self, tmp_path):
        """Test validation fails when too few unique IDs exist."""
        # Setup
        embeddings_dir = tmp_path / "embeddings"
        embeddings_dir.mkdir()
        complexity_csv = tmp_path / "complexity.csv"
        failed_log = tmp_path / "failed.log"

        # Create only 50 valid embedding files
        for i in range(50):
            save_tensor(torch.randn(1, 512), embeddings_dir / f"subject_{i}.pt")

        # Create matching CSV with 50 entries
        csv_data = [{"subject_id": f"subject_{i}", "complexity_score": 0.5} for i in range(50)]
        save_csv(csv_data, complexity_csv)

        # Run validation
        result = validate_unique_ids(embeddings_dir, complexity_csv, failed_log)

        # Assert
        assert result["success"] is False
        assert result["unique_subjects"] == 50
        assert result["min_required"] == MIN_UNIQUE_SUBJECTS
        assert result["failures_count"] == 0

    def test_validation_logs_failures(self, tmp_path):
        """Test that validation logs failures to the specified log file."""
        # Setup
        embeddings_dir = tmp_path / "embeddings"
        embeddings_dir.mkdir()
        complexity_csv = tmp_path / "complexity.csv"
        failed_log = tmp_path / "failed.log"

        # Create 95 valid embedding files
        for i in range(95):
            save_tensor(torch.randn(1, 512), embeddings_dir / f"subject_{i}.pt")

        # Create CSV with only 90 matching IDs (5 missing)
        csv_data = [{"subject_id": f"subject_{i}", "complexity_score": 0.5} for i in range(90)]
        save_csv(csv_data, complexity_csv)

        # Run validation
        result = validate_unique_ids(embeddings_dir, complexity_csv, failed_log)

        # Assert
        assert result["success"] is False  # 90 < 95
        assert result["unique_subjects"] == 90
        assert failed_log.exists()

        # Check log contents
        with open(failed_log, "r") as f:
            lines = f.readlines()
        assert len(lines) > 0  # Should have logged mismatches

    def test_validation_mismatched_ids(self, tmp_path):
        """Test validation handles mismatched IDs between embeddings and CSV."""
        # Setup
        embeddings_dir = tmp_path / "embeddings"
        embeddings_dir.mkdir()
        complexity_csv = tmp_path / "complexity.csv"
        failed_log = tmp_path / "failed.log"

        # Create 100 embedding files with IDs 0-99
        for i in range(100):
            save_tensor(torch.randn(1, 512), embeddings_dir / f"subject_{i}.pt")

        # Create CSV with IDs 50-149 (50 overlap, 50 mismatch)
        csv_data = [{"subject_id": f"subject_{i}", "complexity_score": 0.5} for i in range(50, 150)]
        save_csv(csv_data, complexity_csv)

        # Run validation
        result = validate_unique_ids(embeddings_dir, complexity_csv, failed_log)

        # Assert
        assert result["unique_subjects"] == 50  # Only 50 match
        assert result["success"] is False

    def test_validation_missing_csv(self, tmp_path):
        """Test validation handles missing CSV file."""
        # Setup
        embeddings_dir = tmp_path / "embeddings"
        embeddings_dir.mkdir()
        complexity_csv = tmp_path / "complexity.csv"  # Doesn't exist
        failed_log = tmp_path / "failed.log"

        # Create 100 embedding files
        for i in range(100):
            save_tensor(torch.randn(1, 512), embeddings_dir / f"subject_{i}.pt")

        # Run validation
        result = validate_unique_ids(embeddings_dir, complexity_csv, failed_log)

        # Assert
        assert result["success"] is False
        assert result["unique_subjects"] == 0
        assert result["failures_count"] > 0

    def test_validation_empty_embeddings(self, tmp_path):
        """Test validation handles empty embeddings directory."""
        # Setup
        embeddings_dir = tmp_path / "embeddings"
        embeddings_dir.mkdir()
        complexity_csv = tmp_path / "complexity.csv"
        failed_log = tmp_path / "failed.log"

        # Create CSV with 100 entries
        csv_data = [{"subject_id": f"subject_{i}", "complexity_score": 0.5} for i in range(100)]
        save_csv(csv_data, complexity_csv)

        # Run validation
        result = validate_unique_ids(embeddings_dir, complexity_csv, failed_log)

        # Assert
        assert result["success"] is False
        assert result["unique_subjects"] == 0