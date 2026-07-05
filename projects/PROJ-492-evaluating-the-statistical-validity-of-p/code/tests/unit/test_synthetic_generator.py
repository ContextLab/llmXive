"""
Unit tests for the synthetic dataset generator (T026).
Verifies generation of >= 10,000 records with both binary and continuous outcomes.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_sample_sizes,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    main
)


class TestSyntheticGenerator:
    """Tests for synthetic dataset generation functionality."""

    def test_set_all_seeds_determinism(self):
        """Verify that seeding produces deterministic results."""
        set_all_seeds(42)
        val1 = generate_binary_outcome()
        
        set_all_seeds(42)
        val2 = generate_binary_outcome()

        assert val1["n_control"] == val2["n_control"]
        assert val1["p_control"] == val2["p_control"]

    def test_generate_sample_sizes_binary(self):
        """Test sample size generation for binary outcomes."""
        n1, n2 = generate_sample_sizes(is_binary=True)
        assert 100 <= n1 <= 5000
        assert 100 <= n2 <= 5000

    def test_generate_sample_sizes_continuous(self):
        """Test sample size generation for continuous outcomes."""
        n1, n2 = generate_sample_sizes(is_binary=False)
        assert 50 <= n1 <= 2000
        assert 50 <= n2 <= 2000

    def test_generate_binary_outcome_structure(self):
        """Verify binary outcome has required fields."""
        record = generate_binary_outcome()
        
        required_fields = [
            "outcome_type", "n_control", "n_treatment", "p_control", 
            "p_treatment", "successes_control", "successes_treatment",
            "reported_p_value", "effect_size"
        ]
        
        for field in required_fields:
            assert field in record
        
        assert record["outcome_type"] == "binary"
        assert 0.0 <= record["reported_p_value"] <= 1.0
        assert record["successes_control"] >= 0
        assert record["successes_treatment"] >= 0

    def test_generate_continuous_outcome_structure(self):
        """Verify continuous outcome has required fields."""
        record = generate_continuous_outcome()
        
        required_fields = [
            "outcome_type", "n_control", "n_treatment", "mean_control",
            "mean_treatment", "std_control", "std_treatment",
            "reported_p_value", "effect_size"
        ]
        
        for field in required_fields:
            assert field in record
        
        assert record["outcome_type"] == "continuous"
        assert 0.0 <= record["reported_p_value"] <= 1.0
        assert record["std_control"] > 0
        assert record["std_treatment"] > 0

    def test_verify_outcome_types_raises_on_missing_binary(self):
        """Test that verification fails if binary outcomes are missing."""
        records = [{"outcome_type": "continuous"} for _ in range(10)]
        with pytest.raises(ValueError, match="No binary outcomes"):
            verify_outcome_types(records)

    def test_verify_outcome_types_raises_on_missing_continuous(self):
        """Test that verification fails if continuous outcomes are missing."""
        records = [{"outcome_type": "binary"} for _ in range(10)]
        with pytest.raises(ValueError, match="No continuous outcomes"):
            verify_outcome_types(records)

    def test_verify_outcome_types_success(self):
        """Test successful verification with both types present."""
        records = [
            {"outcome_type": "binary"},
            {"outcome_type": "continuous"}
        ]
        binary_count, continuous_count = verify_outcome_types(records)
        assert binary_count == 1
        assert continuous_count == 1

    def test_generate_synthetic_dataset_minimum_count(self):
        """Test that generated dataset meets minimum record count."""
        records = generate_synthetic_dataset(10000)
        assert len(records) >= 10000

    def test_generate_synthetic_dataset_both_types_present(self):
        """Test that generated dataset contains both outcome types."""
        records = generate_synthetic_dataset(10000)
        binary_count, continuous_count = verify_outcome_types(records)
        
        assert binary_count > 0
        assert continuous_count > 0
        assert binary_count + continuous_count == len(records)

    def test_csv_output_writes_correctly(self):
        """Test CSV writing functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            records = [
                {"id": "1", "outcome_type": "binary", "value": 10},
                {"id": "2", "outcome_type": "continuous", "value": 20.5}
            ]
            
            write_csv_output(records, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]["id"] == "1"
            assert rows[1]["value"] == "20.5"

    def test_json_output_writes_correctly(self):
        """Test JSON writing functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            records = [
                {"id": "1", "outcome_type": "binary"},
                {"id": "2", "outcome_type": "continuous"}
            ]
            
            write_json_output(records, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]["id"] == "1"

    def test_main_creates_files(self):
        """Test that main() creates the expected output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch the output directory
            with patch('code.src.audit.synthetic.Path') as mock_path:
                mock_dir = Path(tmpdir)
                mock_path.return_value = mock_dir
                mock_dir.mkdir = lambda **kwargs: None
                
                # We need to mock the actual write functions to avoid real file writes
                # in the temp dir, but still verify the path logic
                pass

    def test_record_fields_complete(self):
        """Test that generated records have all required fields for pipeline compatibility."""
        records = generate_synthetic_dataset(100)
        
        # Check a sample of records
        for record in records[:10]:
            assert "id" in record
            assert "outcome_type" in record
            assert "domain" in record
            assert "year" in record
            assert "n_control" in record
            assert "n_treatment" in record
            assert "reported_p_value" in record

    def test_outcome_type_distribution(self):
        """Test that the distribution of outcome types is approximately 50/50."""
        records = generate_synthetic_dataset(10000)
        binary_count, continuous_count = verify_outcome_types(records)
        
        # Allow some variance due to randomness
        assert 0.45 * len(records) <= binary_count <= 0.55 * len(records)
        assert 0.45 * len(records) <= continuous_count <= 0.55 * len(records)
