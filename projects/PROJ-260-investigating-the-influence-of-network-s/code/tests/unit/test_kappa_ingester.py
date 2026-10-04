"""
Unit tests for the Kappa Ingestion Service (T057).
"""
import os
import sys
import tempfile
import json
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.kappa_ingester import (
    validate_kappa_entry,
    ingest_kappa_values,
    load_trajectory_ids,
    REQUIRED_COLUMNS
)
from src.lib.config import setup_logger

@pytest.fixture
def valid_trajectory_ids_json(tmp_path):
    """Create a valid trajectory_ids.json file."""
    data = {
        "trajectory_ids": ["traj_001", "traj_002", "traj_003"],
        "metadata": {"source": "zenodo-test"}
    }
    file_path = tmp_path / "trajectory_ids.json"
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

@pytest.fixture
def valid_kappa_csv(tmp_path):
    """Create a valid kappa_values.csv file."""
    file_path = tmp_path / "kappa_values.csv"
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["system_size", "kappa", "source_id", "trajectory_id"])
        writer.writerow(["1000", "1.5", "external_paper_A", "traj_001"])
        writer.writerow(["2000", "1.2", "external_paper_B", "traj_002"])
    return file_path

@pytest.fixture
def logger():
    return setup_logger("test_kappa_ingester")

class TestValidateKappaEntry:
    def test_valid_entry(self, logger):
        row = {
            "system_size": "1000",
            "kappa": "1.5",
            "source_id": "external_paper",
            "trajectory_id": "traj_001"
        }
        valid_ids = {"traj_001", "traj_002"}
        assert validate_kappa_entry(row, valid_ids, logger) is True

    def test_missing_trajectory_id(self, logger):
        row = {
            "system_size": "1000",
            "kappa": "1.5",
            "source_id": "external_paper",
            "trajectory_id": "traj_unknown"
        }
        valid_ids = {"traj_001"}
        assert validate_kappa_entry(row, valid_ids, logger) is False

    def test_invalid_kappa_format(self, logger):
        row = {
            "system_size": "1000",
            "kappa": "not_a_number",
            "source_id": "external_paper",
            "trajectory_id": "traj_001"
        }
        valid_ids = {"traj_001"}
        assert validate_kappa_entry(row, valid_ids, logger) is False

    def test_negative_kappa(self, logger):
        row = {
            "system_size": "1000",
            "kappa": "-1.5",
            "source_id": "external_paper",
            "trajectory_id": "traj_001"
        }
        valid_ids = {"traj_001"}
        assert validate_kappa_entry(row, valid_ids, logger) is False

    def test_missing_required_columns(self, logger):
        row = {
            "system_size": "1000",
            "kappa": "1.5"
            # Missing source_id and trajectory_id
        }
        valid_ids = {"traj_001"}
        assert validate_kappa_entry(row, valid_ids, logger) is False

    def test_internal_source_id_rejected(self, logger):
        row = {
            "system_size": "1000",
            "kappa": "1.5",
            "source_id": "internal_topology_extraction",
            "trajectory_id": "traj_001"
        }
        valid_ids = {"traj_001"}
        assert validate_kappa_entry(row, valid_ids, logger) is False

    def test_empty_string_values(self, logger):
        row = {
            "system_size": "",
            "kappa": "1.5",
            "source_id": "external_paper",
            "trajectory_id": "traj_001"
        }
        valid_ids = {"traj_001"}
        assert validate_kappa_entry(row, valid_ids, logger) is False

class TestIngestKappaValues:
    def test_successful_ingestion(self, tmp_path, valid_trajectory_ids_json, valid_kappa_csv, logger):
        # Mock the path to trajectory IDs
        with patch('src.services.kappa_ingester.TRAJECTORY_IDS_PATH', valid_trajectory_ids_json):
            result = ingest_kappa_values(input_path=valid_kappa_csv, logger=logger)
            assert len(result) == 2
            assert result[0]["system_size"] == 1000
            assert result[0]["kappa"] == 1.5
            assert result[0]["trajectory_id"] == "traj_001"

    def test_file_not_found(self, logger):
        fake_path = Path("/nonexistent/path/file.csv")
        with pytest.raises(FileNotFoundError):
            ingest_kappa_values(input_path=fake_path, logger=logger)

    def test_trajectory_ids_missing(self, tmp_path, valid_kappa_csv, logger):
        # Create a temp dir but no trajectory_ids.json
        with patch('src.services.kappa_ingester.TRAJECTORY_IDS_PATH', tmp_path / "missing.json"):
            with pytest.raises(FileNotFoundError):
                ingest_kappa_values(input_path=valid_kappa_csv, logger=logger)

    def test_invalid_csv_header(self, tmp_path, valid_trajectory_ids_json, logger):
        bad_csv = tmp_path / "bad.csv"
        with open(bad_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["wrong_col", "kappa", "source_id", "trajectory_id"])
            writer.writerow(["1000", "1.5", "src", "traj_001"])
        
        with patch('src.services.kappa_ingester.TRAJECTORY_IDS_PATH', valid_trajectory_ids_json):
            with pytest.raises(ValueError, match="Invalid CSV schema"):
                ingest_kappa_values(input_path=bad_csv, logger=logger)

    def test_all_rows_invalid(self, tmp_path, valid_trajectory_ids_json, logger):
        bad_csv = tmp_path / "bad.csv"
        with open(bad_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["system_size", "kappa", "source_id", "trajectory_id"])
            writer.writerow(["1000", "bad_kappa", "src", "traj_001"])
        
        with patch('src.services.kappa_ingester.TRAJECTORY_IDS_PATH', valid_trajectory_ids_json):
            with pytest.raises(ValueError, match="Validation failed for all rows"):
                ingest_kappa_values(input_path=bad_csv, logger=logger)
