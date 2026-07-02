import json
import csv
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to temporarily adjust the module path to test in isolation
# by mocking the _PROJECT_ROOT or by testing the functions that don't depend on it directly
# However, since the functions write to specific paths, we will test the logic
# by creating a temporary directory structure that mimics the project.

import sys
from unittest.mock import patch, MagicMock

# Add the code directory to the path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

import logging_utils


@pytest.fixture
def temp_project_structure():
    """Create a temporary directory structure mimicking the project."""
    temp_root = tempfile.mkdtemp()
    temp_code = Path(temp_root) / "code"
    temp_logs = Path(temp_root) / "logs"
    temp_code.mkdir()
    temp_logs.mkdir()

    # Patch the _PROJECT_ROOT in logging_utils to point to our temp root
    with patch.object(logging_utils, '_PROJECT_ROOT', Path(temp_root)):
        with patch.object(logging_utils, '_LOGS_DIR', temp_logs):
            with patch.object(logging_utils, '_PAIRING_LOG_PATH', temp_logs / "data_pairing.json"):
                with patch.object(logging_utils, '_FILTERING_LOG_PATH', temp_logs / "feature_filtering.csv"):
                    yield {
                        "root": Path(temp_root),
                        "logs": temp_logs,
                        "pairing_log": temp_logs / "data_pairing.json",
                        "filtering_log": temp_logs / "feature_filtering.csv"
                    }

    shutil.rmtree(temp_root)

def test_log_data_pairing_mismatch(temp_project_structure):
    """Test logging a single pairing mismatch."""
    logging_utils.log_data_pairing_mismatch(
        sample_id="sample_123",
        expression_source="GSE12345",
        metabolite_source="MB12345",
        reason="no_sample_level_pair"
    )

    assert temp_project_structure["pairing_log"].exists()

    with open(temp_project_structure["pairing_log"], 'r') as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["sample_id"] == "sample_123"
    assert data[0]["expression_source"] == "GSE12345"
    assert data[0]["metabolite_source"] == "MB12345"
    assert data[0]["reason"] == "no_sample_level_pair"
    assert "timestamp" in data[0]

def test_log_data_pairing_mismatches_batch(temp_project_structure):
    """Test logging a batch of pairing mismatches."""
    mismatches = [
        {"sample_id": "s1", "expression_source": "e1", "metabolite_source": "m1", "reason": "missing"},
        {"sample_id": "s2", "expression_source": "e2", "metabolite_source": "m2", "reason": "mismatch"}
    ]

    logging_utils.log_data_pairing_mismatches_batch(mismatches)

    with open(temp_project_structure["pairing_log"], 'r') as f:
        data = json.load(f)

    assert len(data) == 2
    assert data[0]["sample_id"] == "s1"
    assert data[1]["sample_id"] == "s2"

def test_get_pairing_log_stats(temp_project_structure):
    """Test getting pairing log statistics."""
    # Initially empty
    stats = logging_utils.get_pairing_log_stats()
    assert stats["total_mismatches"] == 0

    # Add some data
    logging_utils.log_data_pairing_mismatch("s1", "e1", "m1", "reason_a")
    logging_utils.log_data_pairing_mismatch("s2", "e2", "m2", "reason_a")
    logging_utils.log_data_pairing_mismatch("s3", "e3", "m3", "reason_b")

    stats = logging_utils.get_pairing_log_stats()
    assert stats["total_mismatches"] == 3
    assert stats["by_reason"]["reason_a"] == 2
    assert stats["by_reason"]["reason_b"] == 1

def test_log_zero_variance_feature(temp_project_structure):
    """Test logging a single zero-variance feature."""
    logging_utils.log_zero_variance_feature(
        gene_id="AT1G01010",
        variance=0.0,
        reason="zero_variance"
    )

    assert temp_project_structure["filtering_log"].exists()

    with open(temp_project_structure["filtering_log"], 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["gene_id"] == "AT1G01010"
    assert rows[0]["reason"] == "zero_variance"
    assert "timestamp" in rows[0]

def test_log_zero_variance_features_batch(temp_project_structure):
    """Test logging a batch of zero-variance features."""
    features = [
        {"gene_id": "AT1G01010", "variance": 0.0, "reason": "zero_variance"},
        {"gene_id": "AT1G01020", "variance": 1e-15, "reason": "low_variance"}
    ]

    logging_utils.log_zero_variance_features_batch(features)

    with open(temp_project_structure["filtering_log"], 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["gene_id"] == "AT1G01010"
    assert rows[1]["gene_id"] == "AT1G01020"

def test_get_filtering_log_stats(temp_project_structure):
    """Test getting filtering log statistics."""
    # Initially empty
    stats = logging_utils.get_filtering_log_stats()
    assert stats["total_filtered"] == 0

    # Add some data
    logging_utils.log_zero_variance_feature("g1", 0.0, "reason_a")
    logging_utils.log_zero_variance_feature("g2", 0.0, "reason_a")
    logging_utils.log_zero_variance_feature("g3", 1e-12, "reason_b")

    stats = logging_utils.get_filtering_log_stats()
    assert stats["total_filtered"] == 3
    assert stats["by_reason"]["reason_a"] == 2
    assert stats["by_reason"]["reason_b"] == 1

def test_append_to_existing_pairing_log(temp_project_structure):
    """Test that new entries are appended to existing log."""
    # Write initial data
    initial_data = [{"sample_id": "initial", "expression_source": "e", "metabolite_source": "m", "reason": "r"}]
    with open(temp_project_structure["pairing_log"], 'w') as f:
        json.dump(initial_data, f)

    # Add new entry
    logging_utils.log_data_pairing_mismatch("new", "e", "m", "r")

    with open(temp_project_structure["pairing_log"], 'r') as f:
        data = json.load(f)

    assert len(data) == 2
    assert data[0]["sample_id"] == "initial"
    assert data[1]["sample_id"] == "new"

def test_append_to_existing_filtering_log(temp_project_structure):
    """Test that new entries are appended to existing log."""
    # Write initial data with header
    initial_data = "gene_id,variance,reason,timestamp\ng1,0.0,zero_variance,2023-01-01T00:00:00\n"
    with open(temp_project_structure["filtering_log"], 'w') as f:
        f.write(initial_data)

    # Add new entry
    logging_utils.log_zero_variance_feature("g2", 0.0, "zero_variance")

    with open(temp_project_structure["filtering_log"], 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["gene_id"] == "g1"
    assert rows[1]["gene_id"] == "g2"