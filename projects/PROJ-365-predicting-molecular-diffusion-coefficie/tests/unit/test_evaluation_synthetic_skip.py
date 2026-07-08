"""
Unit test for T021b: verify that when the data source is marked as synthetic,
the evaluation step does not create the evaluation JSON report.
"""

import sys
import json
from pathlib import Path

import pytest

# Import the evaluation entry point
from training.evaluate import main as evaluate_main
from utils.config import get_project_root


@pytest.fixture
def synthetic_flag(tmp_path, monkeypatch):
    """
    Create a synthetic data_source_flag.json in the project data directory.
    """
    # Resolve project root using the project's config utility
    project_root = get_project_root()
    data_dir = project_root / "data"
    flag_path = data_dir / "data_source_flag.json"

    # Ensure the data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Write the synthetic flag
    flag_content = {"source": "synthetic"}
    flag_path.write_text(json.dumps(flag_content), encoding="utf-8")

    yield flag_path

    # Cleanup after test
    if flag_path.is_file():
        flag_path.unlink()


@pytest.fixture
def clean_evaluation_file():
    """
    Ensure that the evaluation report does not exist before and after the test.
    """
    project_root = get_project_root()
    eval_path = project_root / "artifacts" / "reports" / "evaluation.json"

    # Ensure the parent directory exists
    eval_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove any pre‑existing file
    if eval_path.is_file():
        eval_path.unlink()

    yield eval_path

    # Cleanup after test
    if eval_path.is_file():
        eval_path.unlink()


def test_evaluation_synthetic_skip(synthetic_flag, clean_evaluation_file, monkeypatch):
    """
    Run the evaluation script with a synthetic data source flag and confirm that
    the evaluation JSON report is not generated.
    """
    # Ensure sys.argv mimics a normal command‑line invocation of the script.
    # The script may accept optional arguments; we provide none to rely on the
    # flag file we just created.
    monkeypatch.setattr(sys, "argv", ["evaluate.py"])

    # Execute the evaluation main function. Any exceptions should cause the test
    # to fail, which is appropriate because the script is expected to handle the
    # synthetic case gracefully.
    evaluate_main()

    # After execution, the evaluation report must not exist.
    assert not clean_evaluation_file.is_file(), (
        f"Evaluation report was created at {clean_evaluation_file} despite "
        "the data source being synthetic."
    )