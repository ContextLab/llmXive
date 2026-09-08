"""
Unit tests for the data ingestion module (code/ingest.py).
"""
import os
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure imports from code/ work
from ingest import (
    setup_logging,
    setup_directories,
    load_and_align_data,
    print_summary,
    parse_args,
    main
)

def test_setup_logging():
    """Test that logging is configured correctly."""
    logger = setup_logging()
    assert logger is not None
    assert logger.name == "ingest"

def test_setup_directories_creates_paths(tmp_path):
    """Test that setup_directories creates the required directory structure."""
    # Mock the project root
    project_root = tmp_path / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"
    project_root.mkdir(parents=True)

    # Call the function
    setup_directories(project_root)

    # Verify directories exist
    assert (project_root / "data" / "raw").exists()
    assert (project_root / "data" / "processed").exists()
    assert (project_root / "results").exists()
    assert (project_root / "code").exists()
    assert (project_root / "tests").exists()

def test_parse_args():
    """Test argument parsing."""
    args = parse_args(["--input", "dummy.parquet", "--output", "dummy_out.parquet"])
    assert args.input == "dummy.parquet"
    assert args.output == "dummy_out.parquet"

def test_load_and_align_data_missing_columns(tmp_path):
    """Test that load_and_align_data raises an error when required columns are missing."""
    # Create a mock dataset with missing columns
    df = pd.DataFrame({
        "prompt": ["test"],
        "image_url": ["http://test.com"]
        # Missing teacher_scores, student_scalar, etc.
    })
    path = tmp_path / "mock.parquet"
    df.to_parquet(path)

    with pytest.raises(RuntimeError, match="Missing required columns"):
        load_and_align_data(path)

def test_load_and_align_data_valid_structure(tmp_path):
    """Test that load_and_align_data processes a valid dataset correctly."""
    # Create a mock dataset with all required columns
    data = {
        "prompt": ["test prompt"],
        "image_url": ["http://test.com"],
        "teacher_scores": [
            {"Alignment": 4.5, "Realism": 3.0, "Aesthetics": 4.0, "Plausibility": 3.5}
        ],
        "student_scalar": [3.8],
        "human_annotations": [
            {"Alignment": 4.0, "Realism": 3.2, "Aesthetics": 4.1, "Plausibility": 3.6}
        ],
        "primary_dimension": ["Alignment"]
    }
    df = pd.DataFrame(data)
    path = tmp_path / "mock.parquet"
    df.to_parquet(path)

    result_df = load_and_align_data(path)

    assert result_df is not None
    assert len(result_df) == 1
    assert "fidelity_loss" in result_df.columns or "excluded_reason" in result_df.columns

def test_print_summary(capsys, tmp_path):
    """Test that print_summary outputs correct summary stats."""
    # Create a mock dataset
    data = {
        "prompt": ["test1", "test2"],
        "image_url": ["http://test.com", "http://test2.com"],
        "teacher_scores": [
            {"Alignment": 4.5, "Realism": 3.0, "Aesthetics": 4.0, "Plausibility": 3.5},
            {"Alignment": 4.0, "Realism": 3.5, "Aesthetics": 3.8, "Plausibility": 4.0}
        ],
        "student_scalar": [3.8, 3.9],
        "human_annotations": [
            {"Alignment": 4.0, "Realism": 3.2, "Aesthetics": 4.1, "Plausibility": 3.6},
            {"Alignment": 3.9, "Realism": 3.4, "Aesthetics": 3.9, "Plausibility": 3.9}
        ],
        "primary_dimension": ["Alignment", "Realism"]
    }
    df = pd.DataFrame(data)
    path = tmp_path / "mock.parquet"
    df.to_parquet(path)

    result_df = load_and_align_data(path)
    print_summary(result_df)

    captured = capsys.readouterr()
    assert "Total samples" in captured.out
    assert "2" in captured.out
