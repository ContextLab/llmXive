"""
Unit tests for the human‑coding preparation script (T002).
"""

import os
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths

# Import the script as a module to test its functions directly
import importlib.util

SPEC_SCRIPT = Path("code/02_prepare_human_coding_dir.py")

spec = importlib.util.spec_from_file_location("prepare_human_coding_dir", SPEC_SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def test_directory_and_files_created(tmp_path, monkeypatch):
    """
    Verify that the script creates the expected directory, README,
    and annotation template with the correct number of rows and columns.
    """
    # Ensure we run in the project root (the test runner already does this)
    # Run the main function
    module.main()

    # 1. Directory exists
    human_dir = paths.data("raw", "human_coding")
    assert human_dir.is_dir(), f"Directory {human_dir} was not created."

    # 2. README exists and contains expected keywords
    readme_path = human_dir / "README.md"
    assert readme_path.is_file(), "README.md missing."
    readme_text = readme_path.read_text(encoding="utf-8")
    assert "Human Coding Annotation Procedure" in readme_text
    assert "three independent annotators" in readme_text.lower()

    # 3. Template CSV exists
    template_path = human_dir / "annotations_template.csv"
    assert template_path.is_file(), "annotations_template.csv missing."

    # Load CSV and verify structure
    df = pd.read_csv(template_path, dtype=str)

    # Expected columns
    expected_columns = ["scenario_id", "annotator_1", "annotator_2", "annotator_3"]
    assert list(df.columns) == expected_columns, "Header columns are incorrect."

    # Verify row count matches candidates file
    candidates_path = paths.processed("candidates_filtered.csv")
    candidates_df = pd.read_csv(candidates_path, dtype=str)
    assert len(df) == len(candidates_df), (
        f"Template rows ({len(df)}) do not match number of scenarios "
        f"({len(candidates_df)})."
    )

    # Ensure scenario IDs match exactly
    assert set(df["scenario_id"]) == set(candidates_df["scenario_id"]), (
        "Mismatch between scenario IDs in template and candidates file."
    )

# The test suite will automatically discover this file via pytest.