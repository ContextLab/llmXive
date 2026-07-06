"""
Unit tests for the synthetic dataset generator (T026).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    write_metadata,
    set_all_seeds
)
from code.src.config import SEED

class TestSyntheticGenerator:
    
    def test_generate_minimal_dataset(self):
        """Test generation of a small dataset to verify logic."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            records = generate_synthetic_dataset(n_records=50, output_dir=output_dir)
            
            assert len(records) == 50
            
            # Check structure
            for r in records:
                assert "id" in r
                assert "outcome_type" in r
                assert r["outcome_type"] in ["binary", "continuous"]
                assert "n_control" in r
                assert "n_treatment" in r
                assert "reported_p_value" in r
                assert "true_p_value" in r
                assert "is_inconsistent" in r

    def test_verify_outcome_types_both_present(self):
        """Test that verify_outcome_types raises if one type is missing."""
        # Test with mixed data
        mixed_data = [
            {"outcome_type": "binary"},
            {"outcome_type": "continuous"}
        ]
        b, c = verify_outcome_types(mixed_data)
        assert b == 1
        assert c == 1

        # Test with only binary (should raise)
        binary_only = [{"outcome_type": "binary"}]
        with pytest.raises(ValueError, match="No continuous outcomes"):
            verify_outcome_types(binary_only)

        # Test with only continuous (should raise)
        continuous_only = [{"outcome_type": "continuous"}]
        with pytest.raises(ValueError, match="No binary outcomes"):
            verify_outcome_types(continuous_only)

    def test_large_dataset_generation(self):
        """Test generation of the full 10,000 record dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            records = generate_synthetic_dataset(n_records=10000, output_dir=output_dir)
            
            assert len(records) >= 10000
            
            binary, continuous = verify_outcome_types(records)
            
            # Ensure significant presence of both types
            assert binary > 1000
            assert continuous > 1000

    def test_output_files_created(self):
        """Test that output files are actually written to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            records = generate_synthetic_dataset(n_records=100, output_dir=output_dir)
            
            csv_path = output_dir / "synthetic_summaries.csv"
            json_path = output_dir / "synthetic_summaries.json"
            meta_path = output_dir / "synthetic_metadata.json"
            
            write_csv_output(records, csv_path)
            write_json_output(records, json_path)
            write_metadata(records, meta_path)
            
            assert csv_path.exists()
            assert json_path.exists()
            assert meta_path.exists()

    def test_csv_content_valid(self):
        """Test that CSV content can be read by pandas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            records = generate_synthetic_dataset(n_records=100, output_dir=output_dir)
            
            csv_path = output_dir / "synthetic_summaries.csv"
            write_csv_output(records, csv_path)
            
            df = pd.read_csv(csv_path)
            assert len(df) == 100
            assert "outcome_type" in df.columns
            assert "reported_p_value" in df.columns

    def test_json_content_valid(self):
        """Test that JSON content is valid and parseable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            records = generate_synthetic_dataset(n_records=100, output_dir=output_dir)
            
            json_path = output_dir / "synthetic_summaries.json"
            write_json_output(records, json_path)
            
            with open(json_path, 'r') as f:
                loaded = json.load(f)
            
            assert len(loaded) == 100
            assert isinstance(loaded[0], dict)

    def test_metadata_content(self):
        """Test that metadata file contains required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            records = generate_synthetic_dataset(n_records=100, output_dir=output_dir)
            
            meta_path = output_dir / "synthetic_metadata.json"
            write_metadata(records, meta_path)
            
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            
            assert "total_records" in meta
            assert "binary_count" in meta
            assert "continuous_count" in meta
            assert meta["binary_count"] + meta["continuous_count"] == 100
            assert meta["seed"] == SEED

    def test_reproducibility(self):
        """Test that setting seeds produces the same results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            set_all_seeds(42)
            records1 = generate_synthetic_dataset(n_records=10, output_dir=output_dir)
            ids1 = [r["id"] for r in records1]
            pvals1 = [r["reported_p_value"] for r in records1]
            
            # Reset seed and regenerate
            set_all_seeds(42)
            records2 = generate_synthetic_dataset(n_records=10, output_dir=output_dir)
            ids2 = [r["id"] for r in records2]
            pvals2 = [r["reported_p_value"] for r in records2]
            
            assert ids1 == ids2
            assert pvals1 == pvals2