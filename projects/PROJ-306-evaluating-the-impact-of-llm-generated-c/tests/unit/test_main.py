import json
import os
import shutil
from pathlib import Path

import pytest

from main import (
    _write_failure_report,
    _process_task,
    main,
)

@pytest.fixture(scope="function")
def clean_coverage_dir(tmp_path):
    """Create a fresh coverage_reports directory for each test."""
    coverage_dir = Path(tmp_path) / "coverage_reports"
    coverage_dir.mkdir(parents=True)
    # Monkey‑patch the path used inside the module to point to the temp dir
    original_dir = Path("data/coverage_reports")
    if original_dir.exists():
        shutil.rmtree(original_dir)
    os.symlink(coverage_dir, original_dir, target_is_directory=True)
    yield coverage_dir
    # Cleanup after test
    if original_dir.is_symlink():
        original_dir.unlink()
    if coverage_dir.exists():
        shutil.rmtree(coverage_dir)

def test_write_failure_report_creates_file(clean_coverage_dir):
    task_id = "test_task_01"
    error_message = "synthetic error for testing"
    _write_failure_report(task_id, error_message)

    report_path = clean_coverage_dir / f"{task_id}.json"
    assert report_path.is_file(), "Failure report file was not created"

    data = json.loads(report_path.read_text())
    assert data["task_id"] == task_id
    assert data["status"] == "failed"
    assert data["error_message"] == error_message
    assert "timestamp" in data

def test_process_task_handles_exception(monkeypatch, clean_coverage_dir):
    # Simulate a task that raises a SyntaxError during generation
    task = {"task_id": "syntax_error_task"}

    def mock_generate_code(*args, **kwargs):
        raise SyntaxError("invalid syntax")

    monkeypatch.setattr("llm_generator.generate_code", mock_generate_code)

    # Process the task – it should not raise, but write a failure report
    _process_task(task)

    report_path = clean_coverage_dir / f"{task['task_id']}.json"
    assert report_path.is_file(), "Failure report not written for SyntaxError"

    data = json.loads(report_path.read_text())
    assert data["status"] == "failed"
    assert "invalid syntax" in data["error_message"]

def test_main_runs_without_crashing(monkeypatch, tmp_path):
    # Prepare a tiny catalog with a single dummy task
    dummy_task = {"task_id": "dummy_001"}
    monkeypatch.setattr("main.load_task_catalog", lambda *args, **kwargs: [dummy_task])

    # Mock generation and coverage so they succeed instantly
    monkeypatch.setattr("llm_generator.generate_code", lambda task_id, model=None: None)
    monkeypatch.setattr(
        "coverage_runner.run_coverage_with_catalog_check",
        lambda task_id: None,
    )

    # Run the CLI entry point with a small batch size
    test_args = ["prog", "--batch-size", "1"]
    monkeypatch.setattr("sys.argv", test_args)

    # Ensure the coverage directory is writable
    (tmp_path / "coverage_reports").mkdir(parents=True)
    monkeypatch.setattr(
        "main.Path",
        lambda *args, **kwargs: Path(tmp_path) / "coverage_reports",
    )

    # Execute main – should complete without raising
    main()

    # Verify that a (potentially empty) JSON file was created for the dummy task
    report_path = Path("data/coverage_reports") / f"{dummy_task['task_id']}.json"
    assert report_path.is_file(), "Coverage report not generated for dummy task"