"""
Unit tests for the Synthetic Dataset Generator (T026).

Verifies:
1. The generator produces at least 10,000 records.
2. Both binary and continuous outcome types are present.
3. The output files are created correctly.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_summaries,
    write_metadata,
    generate_binary_outcome,
    generate_continuous_outcome
)

class TestSyntheticGenerator:
    
    def test_generate_binary_outcome_structure(self):
        """Test that binary outcome generation returns expected keys."""
        data = generate_binary_outcome(100, 100, 0.1, 0.05)
        required_keys = ['x1', 'n1', 'x2', 'n2', 'reported_p_value', 'reported_effect_size', 'is_binary']
        for key in required_keys:
            assert key in data, f"Missing key: {key}"
        assert data['is_binary'] is True
        assert data['n1'] == 100
        assert data['n2'] == 100
    
    def test_generate_continuous_outcome_structure(self):
        """Test that continuous outcome generation returns expected keys."""
        data = generate_continuous_outcome(100, 100, 50.0, 10.0, 5.0)
        required_keys = ['mean1', 'std1', 'n1', 'mean2', 'std2', 'n2', 'reported_p_value', 'is_binary']
        for key in required_keys:
            assert key in data, f"Missing key: {key}"
        assert data['is_binary'] is False
    
    def test_generate_synthetic_dataset_count(self):
        """Test that the dataset generator produces at least 10,000 records."""
        records = generate_synthetic_dataset(total_records=10000)
        assert len(records) >= 10000, f"Expected >= 10000 records, got {len(records)}"
    
    def test_generate_synthetic_dataset_outcome_types(self):
        """Test that both binary and continuous outcomes are generated."""
        records = generate_synthetic_dataset(total_records=10000)
        verification = verify_outcome_types(records)
        
        assert verification['binary_count'] > 0, "No binary records generated"
        assert verification['continuous_count'] > 0, "No continuous records generated"
        assert verification['has_both_outcome_types'] is True
        assert verification['status'] == 'PASSED'
    
    def test_write_summaries_creates_file(self):
        """Test that write_summaries creates a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            records = [
                {'x1': 10, 'n1': 100, 'is_binary': True},
                {'mean1': 5.0, 'n1': 100, 'is_binary': False}
            ]
            write_summaries(records, str(output_path))
            
            assert output_path.exists(), "CSV file was not created"
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
    
    def test_write_metadata_creates_file(self):
        """Test that write_metadata creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_meta.json"
            metadata = {"test": "value", "count": 100}
            write_metadata(metadata, str(output_path))
            
            assert output_path.exists(), "JSON file was not created"
            
            with open(output_path, 'r') as f:
                data = json.load(f)
                assert data['test'] == 'value'
    
    def test_full_generation_pipeline(self):
        """Test the full generation pipeline end-to-end."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "synthetic.csv"
            meta_path = Path(tmpdir) / "meta.json"
            
            records = generate_synthetic_dataset(total_records=10050)
            verification = verify_outcome_types(records)
            
            write_summaries(records, str(csv_path))
            write_metadata(verification, str(meta_path))
            
            # Verify CSV
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) >= 10000
            
            # Verify Metadata
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                assert meta['verification']['status'] == 'PASSED'
                assert meta['verification']['binary_count'] > 0
                assert meta['verification']['continuous_count'] > 0