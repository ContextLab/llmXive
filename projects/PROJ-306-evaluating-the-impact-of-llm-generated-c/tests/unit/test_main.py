"""
Unit tests for the ``code/main.py`` orchestration logic.

The tests use a temporary directory to verify that:

* The argument parser accepts the expected flags.
* A synthetic catalog entry results in a coverage (or failure) JSON file
  being written to the appropriate location.
* Failure handling creates a JSON file with ``status: "failed"``.
"""

import json
import os
import shutil
from pathlib import Path
from unittest import mock

import pytest

from main import build_arg_parser, process_task, batch_process

# Helper to create a minimal catalog file.
def _write_dummy_catalog(tmp_path: Path, entries: list) -> None:
    catalog_dir = Path("data/benchmarks/processed")
    catalog_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = catalog_dir / "catalog.json"
    with catalog_path.open("w", encoding="utf-8") as f:
        json.dump(entries, f)

@pytest.fixture(autouse=True)
def cleanup():
    # Ensure a clean environment for each test.
    yield
    shutil.rmtree("data", ignore_errors=True)

def test_build_arg_parser():
    parser = build_arg_parser()
    args = parser.parse_args(
        ["--dataset", "humaneval", "--model", "test-model", "--batch-size", "5"]
    )
    assert args.dataset == "humaneval"
    assert args.model == "test-model"
    assert args.batch_size == 5

@mock.patch("code.main.generate_code")
@mock.patch("code.main.run_coverage_with_catalog_check")
@mock.patch("code.main.save_coverage_report")
def test_process_task_success(mock_save_report, mock_run_cov, mock_gen_code, tmp_path):
    # Arrange
    dummy_task = {"task_id": "dummy/1"}
    mock_gen_code.return_value = Path("generated/dummy_1.py")
    mock_run_cov.return_value = {"line_coverage": 85, "branch_coverage": "N/A"}

    # Act
    process_task(dummy_task, SimpleNamespace(model_name="test"), Path(tmp_path))

    # Assert
    report_path = Path(tmp_path) / "coverage_reports" / "dummy/1.json"
    assert report_path.is_file()
    with report_path.open() as f:
        data = json.load(f)
    assert data["line_coverage"] == 85

@mock.patch("code.main.generate_code", side_effect=SyntaxError("bad syntax"))
def test_process_task_syntax_error(mock_gen_code, tmp_path):
    dummy_task = {"task_id": "bad/1"}
    process_task(dummy_task, SimpleNamespace(model_name="test"), Path(tmp_path))

    report_path = Path(tmp_path) / "coverage_reports" / "bad/1.json"
    assert report_path.is_file()
    with report_path.open() as f:
        data = json.load(f)
    assert data["status"] == "failed"
    assert "SyntaxError" in data["error_message"]