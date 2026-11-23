"""
Unit tests for T028b: Sensitivity Metadata Recorder

Tests the functionality of sensitivity_metadata_recorder.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.sensitivity_metadata_recorder import (
    load_sensitivity_density_sweep,
    create_perturbation_config_from_row,
    record_metadata,
    run_sensitivity_metadata_recorder
)
from data_models import PerturbationConfig


class TestLoadSensitivityDensitySweep:
    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        csv_path = tmp_path / 'test_sweep.csv'
        content = """run_id,density,rank,type,theta_c,seed
        run_1,0.2,1,diagonal,2.5,42
        run_2,0.3,1,diagonal,2.6,123
        """
        csv_path.write_text(content)

        results = load_sensitivity_density_sweep(csv_path)

        assert len(results) == 2
        assert results[0]['run_id'] == 'run_1'
        assert results[0]['density'] == 0.2
        assert results[0]['rank'] == 1
        assert results[0]['type'] == 'diagonal'
        assert results[0]['theta_c'] == 2.5
        assert results[0]['seed'] == 42

    def test_load_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        csv_path = tmp_path / 'nonexistent.csv'

        with pytest.raises(FileNotFoundError):
            load_sensitivity_density_sweep(csv_path)

    def test_load_empty_csv(self, tmp_path):
        """Test loading an empty CSV (only headers)."""
        csv_path = tmp_path / 'empty.csv'
        csv_path.write_text("run_id,density,rank,type,theta_c,seed\n")

        results = load_sensitivity_density_sweep(csv_path)
        assert len(results) == 0


class TestCreatePerturbationConfigFromRow:
    def test_create_config_diagonal(self):
        """Test creating config for diagonal perturbation."""
        row = {
            'run_id': 'test_run',
            'rank': 1,
            'density': 0.5,
            'type': 'diagonal',
            'seed': 42
        }

        config = create_perturbation_config_from_row(row)

        assert isinstance(config, PerturbationConfig)
        assert config.run_id == 'test_run'
        assert config.rank == 1
        assert config.support_density == 0.5
        assert config.type == 'diagonal'
        assert config.seed == 42

    def test_create_config_block_sparse(self):
        """Test creating config for block-sparse perturbation."""
        row = {
            'run_id': 'block_run',
            'rank': 2,
            'density': 0.3,
            'type': 'block-sparse',
            'seed': 123
        }

        config = create_perturbation_config_from_row(row)

        assert config.type == 'block-sparse'
        assert config.rank == 2

    def test_create_config_random_sparse(self):
        """Test creating config for random sparse perturbation."""
        row = {
            'run_id': 'random_run',
            'rank': 3,
            'density': 0.1,
            'type': 'random sparse',
            'seed': 456
        }

        config = create_perturbation_config_from_row(row)

        assert config.type == 'random sparse'
        assert config.rank == 3

    def test_create_config_unknown_type(self):
        """Test that unknown type defaults to diagonal with warning."""
        row = {
            'run_id': 'unknown_run',
            'rank': 1,
            'density': 0.2,
            'type': 'unknown_type',
            'seed': 789
        }

        # Should not raise, should default to diagonal
        config = create_perturbation_config_from_row(row)
        assert config.type == 'diagonal'

    def test_create_config_missing_optional_fields(self):
        """Test creating config with missing optional fields."""
        row = {
            'run_id': 'minimal_run',
            'rank': 1,
            'density': 0.2
        }

        config = create_perturbation_config_from_row(row)

        assert config.run_id == 'minimal_run'
        assert config.rank == 1
        assert config.support_density == 0.2
        # Optional fields should be None
        assert config.theta is None
        assert config.N is None


class TestRecordMetadata:
    def test_record_single_config(self, tmp_path):
        """Test recording a single config."""
        config = PerturbationConfig(
            run_id='test_1',
            rank=1,
            support_density=0.2,
            type='diagonal',
            seed=42
        )

        output_path = tmp_path / 'metadata.json'
        record_metadata([config], output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]['run_id'] == 'test_1'
        assert data[0]['rank'] == 1
        assert data[0]['support_density'] == 0.2

    def test_record_multiple_configs(self, tmp_path):
        """Test recording multiple configs."""
        configs = [
            PerturbationConfig(run_id='test_1', rank=1, support_density=0.2, type='diagonal', seed=42),
            PerturbationConfig(run_id='test_2', rank=2, support_density=0.3, type='block-sparse', seed=123),
            PerturbationConfig(run_id='test_3', rank=3, support_density=0.1, type='random sparse', seed=456)
        ]

        output_path = tmp_path / 'metadata.json'
        record_metadata(configs, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert len(data) == 3
        assert data[0]['run_id'] == 'test_1'
        assert data[1]['run_id'] == 'test_2'
        assert data[2]['run_id'] == 'test_3'

    def test_record_empty_list(self, tmp_path):
        """Test recording an empty list."""
        output_path = tmp_path / 'metadata.json'
        record_metadata([], output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert data == []


class TestRunSensitivityMetadataRecorder:
    def test_full_run(self, tmp_path):
        """Test the full recorder workflow."""
        # Create input CSV
        input_csv = tmp_path / 'sensitivity_density_sweep.csv'
        input_csv.write_text("""run_id,density,rank,type,theta_c,seed
        run_1,0.2,1,diagonal,2.5,42
        run_2,0.3,1,block-sparse,2.6,123
        run_3,0.4,2,random sparse,2.7,456
        """)

        output_json = tmp_path / 'sensitivity_metadata.json'

        run_sensitivity_metadata_recorder(input_csv, output_json)

        assert output_json.exists()

        with open(output_json, 'r') as f:
            data = json.load(f)

        assert len(data) == 3
        assert data[0]['run_id'] == 'run_1'
        assert data[0]['support_density'] == 0.2
        assert data[0]['type'] == 'diagonal'
        assert data[1]['run_id'] == 'run_2'
        assert data[1]['type'] == 'block-sparse'
        assert data[2]['run_id'] == 'run_3'
        assert data[2]['rank'] == 2
        assert data[2]['type'] == 'random sparse'

    def test_full_run_no_input(self, tmp_path):
        """Test that an empty metadata file is created when input is missing."""
        input_csv = tmp_path / 'nonexistent.csv'
        output_json = tmp_path / 'metadata.json'

        run_sensitivity_metadata_recorder(input_csv, output_json)

        assert output_json.exists()

        with open(output_json, 'r') as f:
            data = json.load(f)

        assert data == []