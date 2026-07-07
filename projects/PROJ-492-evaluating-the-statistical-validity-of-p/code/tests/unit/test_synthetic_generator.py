"""
Unit tests for the synthetic dataset generator (T026).
Verifies generation of >= 10,000 records and presence of both outcome types.
"""
import csv
import json
import sys
from pathlib import Path
from datetime import datetime

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_metadata,
    set_all_seeds,
    generate_binary_outcome,
    generate_continuous_outcome
)
from code.src.config import SEED

class TestSyntheticGenerator:
    """Tests for synthetic dataset generation."""

    def test_generate_binary_outcome_structure(self):
        """Test that binary outcome generation returns required fields."""
        record = generate_binary_outcome()
        
        required_fields = [
            "outcome_type", "n_control", "n_treatment", 
            "baseline_rate", "treatment_rate", 
            "successes_control", "successes_treatment",
            "reported_p_value", "effect_size"
        ]
        
        for field in required_fields:
            assert field in record, f"Missing field: {field}"
        
        assert record["outcome_type"] == "binary"
        assert isinstance(record["n_control"], int)
        assert isinstance(record["n_treatment"], int)
        assert 0.0 <= record["baseline_rate"] <= 1.0
        assert 0.0 <= record["treatment_rate"] <= 1.0

    def test_generate_continuous_outcome_structure(self):
        """Test that continuous outcome generation returns required fields."""
        record = generate_continuous_outcome()
        
        required_fields = [
            "outcome_type", "n_control", "n_treatment",
            "baseline_mean", "treatment_mean",
            "baseline_std", "treatment_std",
            "reported_p_value", "effect_size"
        ]
        
        for field in required_fields:
            assert field in record, f"Missing field: {field}"
        
        assert record["outcome_type"] == "continuous"
        assert isinstance(record["n_control"], int)
        assert isinstance(record["n_treatment"], int)
        assert record["baseline_std"] > 0
        assert record["treatment_std"] > 0

    def test_verify_outcome_types_both_present(self):
        """Test verification function with mixed dataset."""
        # Manually create a mixed list
        records = [
            {"outcome_type": "binary", "id": "1"},
            {"outcome_type": "continuous", "id": "2"},
            {"outcome_type": "binary", "id": "3"}
        ]
        
        binary_count, continuous_count, has_both = verify_outcome_types(records)
        
        assert binary_count == 2
        assert continuous_count == 1
        assert has_both is True

    def test_verify_outcome_types_missing_type_raises(self):
        """Test that verification fails if one type is missing."""
        records = [
            {"outcome_type": "binary", "id": "1"},
            {"outcome_type": "binary", "id": "2"}
        ]
        
        with pytest.raises(ValueError, match="must contain both binary and continuous"):
            verify_outcome_types(records)

    def test_generate_synthetic_dataset_count(self):
        """Test that the generator produces at least 10,000 records."""
        set_all_seeds()
        records = generate_synthetic_dataset(count=10000)
        
        assert len(records) >= 10000, f"Expected >= 10000, got {len(records)}"

    def test_generate_synthetic_dataset_outcome_types(self):
        """Test that the generator produces both outcome types."""
        set_all_seeds()
        records = generate_synthetic_dataset(count=10000)
        
        binary_count, continuous_count, has_both = verify_outcome_types(records)
        
        assert has_both is True
        assert binary_count > 0
        assert continuous_count > 0

    def test_write_csv_output(self, tmp_path):
        """Test CSV writing functionality."""
        set_all_seeds()
        records = generate_synthetic_dataset(count=100)
        
        output_path = tmp_path / "test_output.csv"
        write_csv_output(records, output_path)
        
        assert output_path.exists()
        
        # Verify CSV content
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 100
        assert "outcome_type" in rows[0]
        assert "id" in rows[0]

    def test_write_metadata(self, tmp_path):
        """Test metadata writing functionality."""
        set_all_seeds()
        records = generate_synthetic_dataset(count=100)
        
        write_metadata(records, tmp_path)
        
        metadata_path = tmp_path / "synthetic_metadata.json"
        assert metadata_path.exists()
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        assert metadata["total_records"] == 100
        assert "binary_count" in metadata
        assert "continuous_count" in metadata
        assert metadata["seed"] == SEED

    def test_full_integration(self, tmp_path):
        """Test the full generation pipeline end-to-end."""
        set_all_seeds()
        records = generate_synthetic_dataset(count=10000)
        
        # Verify counts
        assert len(records) >= 10000
        
        binary_count, continuous_count, has_both = verify_outcome_types(records)
        assert has_both is True
        
        # Write outputs
        csv_path = tmp_path / "synthetic_summaries.csv"
        write_csv_output(records, csv_path)
        
        write_metadata(records, tmp_path)
        
        # Verify files exist and are valid
        assert csv_path.exists()
        assert (tmp_path / "synthetic_metadata.json").exists()
        
        # Verify CSV row count
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
        
        assert len(csv_rows) == 10000
        
        # Verify outcome distribution in CSV
        csv_binary = sum(1 for r in csv_rows if r["outcome_type"] == "binary")
        csv_continuous = sum(1 for r in csv_rows if r["outcome_type"] == "continuous")
        
        assert csv_binary == binary_count
        assert csv_continuous == continuous_count