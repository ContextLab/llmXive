"""
Unit tests for generate_ground_truth.py
"""

import csv
import os
import tempfile
from pathlib import Path

import pytest

# Import the main function and dependencies
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from dataset.generate_ground_truth import main as generate_main
from config import Paths


@pytest.fixture
def sample_annotation_sample(tmp_path):
    """Create a temporary annotation sample CSV for testing."""
    input_file = tmp_path / "annotation_sample.csv"
    data = [
        {"task_id": "task_001", "raw_prompt": "Do X", "constraint_list": "c1,c2", "constraint_count": "2"},
        {"task_id": "task_002", "raw_prompt": "Do Y", "constraint_list": "c3", "constraint_count": "1"},
        {"task_id": "task_003", "raw_prompt": "Do Z", "constraint_list": "c4,c5,c6", "constraint_count": "3"},
    ]

    with open(input_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    return input_file


@pytest.fixture
def empty_annotation_sample(tmp_path):
    """Create an empty annotation sample CSV (header only) for testing."""
    input_file = tmp_path / "annotation_sample_empty.csv"
    with open(input_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "raw_prompt", "constraint_list", "constraint_count"])
        writer.writeheader()
    return input_file


def test_generate_ground_truth_creates_file(sample_annotation_sample, tmp_path):
    """Test that the script creates the output file."""
    output_file = tmp_path / "annotation_labels.csv"

    # Run the script
    sys.argv = ["generate_ground_truth.py", "--input", str(sample_annotation_sample), "--output", str(output_file)]
    generate_main()

    assert output_file.exists(), "Output file was not created."


def test_generate_ground_truth_columns(sample_annotation_sample, tmp_path):
    """Test that the output file has the correct columns."""
    output_file = tmp_path / "annotation_labels.csv"

    sys.argv = ["generate_ground_truth.py", "--input", str(sample_annotation_sample), "--output", str(output_file)]
    generate_main()

    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

    expected_headers = ["task_id", "raw_prompt", "constraint_list", "constraint_count", "is_violation", "is_implicit"]
    assert list(headers) == expected_headers, f"Headers mismatch. Expected {expected_headers}, got {list(headers)}"


def test_generate_ground_truth_placeholder_values(sample_annotation_sample, tmp_path):
    """Test that the placeholder columns are empty strings."""
    output_file = tmp_path / "annotation_labels.csv"

    sys.argv = ["generate_ground_truth.py", "--input", str(sample_annotation_sample), "--output", str(output_file)]
    generate_main()

    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3, "Row count mismatch."

    for row in rows:
        assert row["is_violation"] == "", f"is_violation should be empty, got '{row['is_violation']}'"
        assert row["is_implicit"] == "", f"is_implicit should be empty, got '{row['is_implicit']}'"


def test_generate_ground_truth_preserves_original_data(sample_annotation_sample, tmp_path):
    """Test that original data is preserved in the output."""
    output_file = tmp_path / "annotation_labels.csv"

    sys.argv = ["generate_ground_truth.py", "--input", str(sample_annotation_sample), "--output", str(output_file)]
    generate_main()

    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Check first row
    assert rows[0]["task_id"] == "task_001"
    assert rows[0]["raw_prompt"] == "Do X"
    assert rows[0]["constraint_list"] == "c1,c2"
    assert rows[0]["constraint_count"] == "2"


def test_generate_ground_truth_empty_input(empty_annotation_sample, tmp_path):
    """Test behavior with an empty input file (header only)."""
    output_file = tmp_path / "annotation_labels_empty.csv"

    sys.argv = ["generate_ground_truth.py", "--input", str(empty_annotation_sample), "--output", str(output_file)]
    generate_main()

    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 0, "Empty input should result in empty output rows."


def test_generate_ground_truth_missing_input(tmp_path):
    """Test error handling when input file is missing."""
    non_existent = tmp_path / "non_existent.csv"
    output_file = tmp_path / "output.csv"

    with pytest.raises(SystemExit) as excinfo:
        sys.argv = ["generate_ground_truth.py", "--input", str(non_existent), "--output", str(output_file)]
        generate_main()

    assert excinfo.value.code == 1