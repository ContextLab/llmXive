import csv
import os
import tempfile
from pathlib import Path
import pytest

from generation.pipeline import filter_valid_samples

def create_test_samples_csv(temp_dir: Path, rows: list) -> Path:
    """Helper to create a test CSV file."""
    csv_path = temp_dir / "samples_all.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if rows:
            fieldnames = list(rows[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        else:
            # Empty file with headers
            writer = csv.DictWriter(f, fieldnames=["task_id", "style", "sample_id", "code", "pass_status"])
            writer.writeheader()
    return csv_path

def test_filter_valid_samples_basic(tmp_path):
    """Test basic filtering of valid samples."""
    data = [
        {"task_id": "1", "style": "pep8", "sample_id": "1", "code": "def f(): pass", "pass_status": "True"},
        {"task_id": "1", "style": "pep8", "sample_id": "2", "code": "def f(): pass", "pass_status": "False"},
        {"task_id": "2", "style": "minified", "sample_id": "1", "code": "def f():pass", "pass_status": "True"},
        {"task_id": "2", "style": "minified", "sample_id": "2", "code": "def f():pass", "pass_status": None},
    ]
    input_path = create_test_samples_csv(tmp_path, data)
    output_path = tmp_path / "samples_valid.csv"

    filter_valid_samples(input_path, output_path)

    assert output_path.exists()
    with open(output_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert all(r["pass_status"] == "True" for r in rows)
    task_ids = {r["task_id"] for r in rows}
    assert task_ids == {"1", "2"}

def test_filter_valid_samples_no_valid(tmp_path):
    """Test filtering when no samples are valid."""
    data = [
        {"task_id": "1", "style": "pep8", "sample_id": "1", "code": "def f(): pass", "pass_status": "False"},
        {"task_id": "1", "style": "pep8", "sample_id": "2", "code": "def f(): pass", "pass_status": None},
    ]
    input_path = create_test_samples_csv(tmp_path, data)
    output_path = tmp_path / "samples_valid.csv"

    filter_valid_samples(input_path, output_path)

    assert output_path.exists()
    with open(output_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 0

def test_filter_valid_samples_missing_file(tmp_path):
    """Test that FileNotFoundError is raised if input file is missing."""
    input_path = tmp_path / "nonexistent.csv"
    output_path = tmp_path / "samples_valid.csv"

    with pytest.raises(FileNotFoundError):
        filter_valid_samples(input_path, output_path)

def test_filter_valid_samples_missing_column(tmp_path):
    """Test that ValueError is raised if pass_status column is missing."""
    csv_path = tmp_path / "samples_all.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "style"])
        writer.writeheader()
        writer.writerow({"task_id": "1", "style": "pep8"})

    output_path = tmp_path / "samples_valid.csv"

    with pytest.raises(ValueError):
        filter_valid_samples(csv_path, output_path)