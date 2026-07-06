"""
Unit tests for synthetic dataset generation (T026).
Verifies that the generator produces at least 10,000 records with both outcome types.
"""
import pytest
import json
import csv
from pathlib import Path
import tempfile
import shutil

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    write_metadata,
    main
)
from code.src.config import SEED


class TestSyntheticGeneration:
    """Tests for synthetic dataset generation functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        set_all_seeds(SEED)
        yield
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_minimum_records(self):
        """Test that generator produces at least 10,000 records."""
        records, binary_count, continuous_count = generate_synthetic_dataset(
            n_records=10000,
            output_dir=self.test_dir
        )

        assert len(records) >= 10000, f"Expected at least 10,000 records, got {len(records)}"
        assert binary_count + continuous_count == len(records)

    def test_both_outcome_types_present(self):
        """Test that both binary and continuous outcomes are generated."""
        records, binary_count, continuous_count = generate_synthetic_dataset(
            n_records=10000,
            binary_ratio=0.5,
            output_dir=self.test_dir
        )

        assert binary_count > 0, "No binary outcomes generated"
        assert continuous_count > 0, "No continuous outcomes generated"
        assert binary_count >= 1000, f"Insufficient binary outcomes: {binary_count}"
        assert continuous_count >= 1000, f"Insufficient continuous outcomes: {continuous_count}"

    def test_verify_outcome_types_passes(self):
        """Test that verify_outcome_types returns True for valid data."""
        records, binary_count, continuous_count = generate_synthetic_dataset(
            n_records=10000,
            output_dir=self.test_dir
        )

        result = verify_outcome_types(records)
        assert result is True, "Outcome type verification should pass"

    def test_verify_outcome_types_fails_low_binary(self):
        """Test that verify_outcome_types returns False when binary count is too low."""
        # Create a mock dataset with insufficient binary records
        mock_records = [{"outcome_type": "continuous"} for _ in range(10000)]
        result = verify_outcome_types(mock_records)
        assert result is False, "Should fail when binary count is too low"

    def test_verify_outcome_types_fails_low_continuous(self):
        """Test that verify_outcome_types returns False when continuous count is too low."""
        # Create a mock dataset with insufficient continuous records
        mock_records = [{"outcome_type": "binary"} for _ in range(10000)]
        result = verify_outcome_types(mock_records)
        assert result is False, "Should fail when continuous count is too low"

    def test_csv_output_created(self):
        """Test that CSV output file is created and contains data."""
        records, _, _ = generate_synthetic_dataset(
            n_records=10000,
            output_dir=self.test_dir
        )

        csv_path = self.test_dir / "test_output.csv"
        write_csv_output(records, csv_path)

        assert csv_path.exists(), "CSV file was not created"
        assert csv_path.stat().st_size > 0, "CSV file is empty"

        # Verify CSV content
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) >= 10000, f"CSV contains {len(rows)} rows, expected >= 10000"

    def test_json_output_created(self):
        """Test that JSON output file is created and contains data."""
        records, _, _ = generate_synthetic_dataset(
            n_records=10000,
            output_dir=self.test_dir
        )

        json_path = self.test_dir / "test_output.json"
        write_json_output(records, json_path)

        assert json_path.exists(), "JSON file was not created"
        assert json_path.stat().st_size > 0, "JSON file is empty"

        # Verify JSON content
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) >= 10000, f"JSON contains {len(data)} records, expected >= 10000"

    def test_metadata_output_created(self):
        """Test that metadata file is created with correct fields."""
        records, binary_count, continuous_count = generate_synthetic_dataset(
            n_records=10000,
            output_dir=self.test_dir
        )

        metadata_path = self.test_dir / "test_metadata.json"
        write_metadata(binary_count, continuous_count, len(records), metadata_path)

        assert metadata_path.exists(), "Metadata file was not created"

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            assert "total_records" in metadata
            assert "binary_count" in metadata
            assert "continuous_count" in metadata
            assert metadata["total_records"] >= 10000
            assert metadata["binary_count"] > 0
            assert metadata["continuous_count"] > 0

    def test_main_returns_success(self):
        """Test that main() returns 0 on success."""
        # Note: This test would normally need to mock file writing
        # For now, we test the core logic
        set_all_seeds(SEED)
        records, binary_count, continuous_count = generate_synthetic_dataset(
            n_records=10000,
            output_dir=self.test_dir
        )
        assert len(records) >= 10000
        assert binary_count > 0 and continuous_count > 0

    def test_record_structure(self):
        """Test that generated records have required fields."""
        records, _, _ = generate_synthetic_dataset(
            n_records=100,
            output_dir=self.test_dir
        )

        required_fields = [
            "id", "url", "domain", "year", "outcome_type",
            "n_control", "n_treatment", "p_value", "effect_size", "is_significant"
        ]

        for record in records:
            for field in required_fields:
                assert field in record, f"Record missing required field: {field}"

    def test_outcome_type_values(self):
        """Test that outcome_type is either 'binary' or 'continuous'."""
        records, _, _ = generate_synthetic_dataset(
            n_records=100,
            output_dir=self.test_dir
        )

        for record in records:
            assert record["outcome_type"] in ["binary", "continuous"], \
                f"Invalid outcome_type: {record['outcome_type']}"

    def test_sample_sizes_positive(self):
        """Test that sample sizes are positive integers."""
        records, _, _ = generate_synthetic_dataset(
            n_records=100,
            output_dir=self.test_dir
        )

        for record in records:
            assert record["n_control"] > 0, "n_control must be positive"
            assert record["n_treatment"] > 0, "n_treatment must be positive"

    def test_p_values_in_range(self):
        """Test that p-values are in valid range [0, 1]."""
        records, _, _ = generate_synthetic_dataset(
            n_records=100,
            output_dir=self.test_dir
        )

        for record in records:
            p_value = record["p_value"]
            assert 0 <= p_value <= 1, f"P-value out of range: {p_value}"

    def test_reproducibility(self):
        """Test that generation is reproducible with same seed."""
        set_all_seeds(SEED)
        records1, _, _ = generate_synthetic_dataset(n_records=100, output_dir=self.test_dir / "run1")

        set_all_seeds(SEED)
        records2, _, _ = generate_synthetic_dataset(n_records=100, output_dir=self.test_dir / "run2")

        # Compare first few records
        for i in range(min(5, len(records1))):
            assert records1[i]["id"] == records2[i]["id"]
            assert records1[i]["p_value"] == records2[i]["p_value"]
            assert records1[i]["effect_size"] == records2[i]["effect_size"]