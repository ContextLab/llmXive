"""
Unit tests for the synthetic dataset generator.
Verifies FR-030 requirements: 10,000+ records with both binary and continuous outcomes.
"""
import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

from code.src.audit.synthetic import (
    set_all_seeds,
    generate_sample_sizes,
    generate_binary_outcome,
    generate_continuous_outcome,
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output
)
from code.src.config import SEED


class TestSyntheticGenerator:
    """Test suite for synthetic dataset generation."""

    def test_set_all_seeds(self):
        """Test that all random seeds are set correctly."""
        set_all_seeds(42)
        # Verify reproducibility
        val1 = np.random.random()
        set_all_seeds(42)
        val2 = np.random.random()
        assert val1 == val2, "Seeds not set correctly"

    def test_generate_sample_sizes(self):
        """Test sample size generation produces valid ranges."""
        n_control, n_treatment = generate_sample_sizes(min_n=100, max_n=1000)
        assert 100 <= n_control <= 1000
        assert 100 <= n_treatment <= 1200  # Up to 120% of control

    def test_generate_binary_outcome(self):
        """Test binary outcome generation produces valid data."""
        data = generate_binary_outcome(1000, 1000, baseline_rate=0.2, effect_size=0.05)
        
        assert data['outcome_type'] == 'binary'
        assert data['n_control'] == 1000
        assert data['n_treatment'] == 1000
        assert 0 <= data['successes_control'] <= data['n_control']
        assert 0 <= data['successes_treatment'] <= data['n_treatment']
        assert 0 <= data['rate_control'] <= 1
        assert 0 <= data['rate_treatment'] <= 1
        assert 0 <= data['p_value_true'] <= 1

    def test_generate_continuous_outcome(self):
        """Test continuous outcome generation produces valid data."""
        data = generate_continuous_outcome(1000, 1000, baseline_mean=50, baseline_std=10)
        
        assert data['outcome_type'] == 'continuous'
        assert data['n_control'] == 1000
        assert data['n_treatment'] == 1000
        assert data['mean_control'] > 0
        assert data['mean_treatment'] > 0
        assert data['std_control'] > 0
        assert data['std_treatment'] > 0
        assert 0 <= data['p_value_true'] <= 1

    def test_generate_synthetic_dataset_creates_files(self):
        """Test that dataset generation creates output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "synthetic"
            metadata = generate_synthetic_dataset(
                n_records=100,
                output_dir=str(output_dir),
                seed=42
            )
            
            assert output_dir.exists()
            assert (output_dir / "synthetic_summaries.csv").exists()
            assert (output_dir / "synthetic_summaries.json").exists()
            assert (output_dir / "synthetic_metadata.json").exists()

    def test_generate_synthetic_dataset_minimum_records(self):
        """Test that dataset meets minimum record count (FR-030)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "synthetic"
            metadata = generate_synthetic_dataset(
                n_records=10000,
                output_dir=str(output_dir),
                seed=42
            )
            
            assert metadata['total_records'] >= 10000
            
            # Verify CSV file has correct record count
            csv_path = output_dir / "synthetic_summaries.csv"
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                records = list(reader)
            
            assert len(records) >= 10000

    def test_verify_outcome_types_both_present(self):
        """Test verification passes when both outcome types are present."""
        records = [
            {'outcome_type': 'binary', 'id': 1},
            {'outcome_type': 'continuous', 'id': 2},
            {'outcome_type': 'binary', 'id': 3}
        ]
        
        binary_count, continuous_count = verify_outcome_types(records)
        
        assert binary_count == 2
        assert continuous_count == 1

    def test_verify_outcome_types_missing_binary(self):
        """Test verification fails when binary outcomes are missing."""
        records = [
            {'outcome_type': 'continuous', 'id': 1},
            {'outcome_type': 'continuous', 'id': 2}
        ]
        
        with pytest.raises(ValueError, match="No binary outcomes"):
            verify_outcome_types(records)

    def test_verify_outcome_types_missing_continuous(self):
        """Test verification fails when continuous outcomes are missing."""
        records = [
            {'outcome_type': 'binary', 'id': 1},
            {'outcome_type': 'binary', 'id': 2}
        ]
        
        with pytest.raises(ValueError, match="No continuous outcomes"):
            verify_outcome_types(records)

    def test_generate_synthetic_dataset_both_outcome_types(self):
        """Test that generated dataset contains both outcome types (FR-030)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "synthetic"
            metadata = generate_synthetic_dataset(
                n_records=10000,
                output_dir=str(output_dir),
                seed=42
            )
            
            assert metadata['binary_count'] > 0
            assert metadata['continuous_count'] > 0
            assert metadata['binary_count'] + metadata['continuous_count'] == metadata['total_records']

    def test_csv_output_format(self):
        """Test CSV output has correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.csv"
            records = [
                {'id': '1', 'value': 10, 'outcome_type': 'binary'},
                {'id': '2', 'value': 20, 'outcome_type': 'continuous'}
            ]
            
            write_csv_output(records, output_path)
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert 'id' in rows[0]
            assert 'value' in rows[0]
            assert 'outcome_type' in rows[0]

    def test_json_output_format(self):
        """Test JSON output has correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            records = [
                {'id': '1', 'value': 10},
                {'id': '2', 'value': 20}
            ]
            
            write_json_output(records, output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]['id'] == '1'
            assert data[1]['id'] == '2'

    def test_metadata_structure(self):
        """Test that metadata contains all required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "synthetic"
            metadata = generate_synthetic_dataset(
                n_records=100,
                output_dir=str(output_dir),
                seed=42
            )
            
            required_fields = [
                'generated_at', 'total_records', 'binary_count',
                'continuous_count', 'inconsistent_count', 'inconsistency_rate',
                'seed', 'output_files'
            ]
            
            for field in required_fields:
                assert field in metadata, f"Missing required field: {field}"

    def test_reproducibility(self):
        """Test that same seed produces identical results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir1 = Path(tmpdir) / "synthetic1"
            output_dir2 = Path(tmpdir) / "synthetic2"
            
            metadata1 = generate_synthetic_dataset(
                n_records=100,
                output_dir=str(output_dir1),
                seed=12345
            )
            
            metadata2 = generate_synthetic_dataset(
                n_records=100,
                output_dir=str(output_dir2),
                seed=12345
            )
            
            assert metadata1['binary_count'] == metadata2['binary_count']
            assert metadata1['continuous_count'] == metadata2['continuous_count']

    def test_inconsistency_injection(self):
        """Test that inconsistency injection works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "synthetic"
            metadata = generate_synthetic_dataset(
                n_records=1000,
                output_dir=str(output_dir),
                seed=42,
                inconsistency_rate=0.5
            )
            
            # Should have approximately 50% inconsistencies
            assert 0.4 < metadata['inconsistency_rate'] < 0.6
