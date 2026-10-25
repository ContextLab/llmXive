"""
Unit tests for dataset design verification.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from code.datasets.verify_design import verify_dataset_design

def test_missing_directory(tmp_path):
    with patch("code.datasets.verify_design.paths.data") as mock_paths:
        mock_paths.return_value = tmp_path / "nonexistent"
        success, reason = verify_dataset_design("ds000001")
        assert success is False
        assert reason == "dataset_directory_missing"

def test_invalid_json_description(tmp_path):
    # Setup: create directory and an invalid JSON file
    ds_dir = tmp_path / "ds000001"
    ds_dir.mkdir(parents=True)
    desc_file = ds_dir / "dataset_description.json"
    desc_file.write_text("<html>Not JSON</html>")

    with patch("code.datasets.verify_design.paths.data") as mock_paths:
        mock_paths.return_value = ds_dir
        success, reason = verify_dataset_design("ds000001")
        assert success is False
        assert reason == "invalid_json_description"

def test_missing_mindfulness_keywords(tmp_path):
    # Setup: valid JSON but no mindfulness keywords
    ds_dir = tmp_path / "ds000001"
    ds_dir.mkdir(parents=True)
    desc_file = ds_dir / "dataset_description.json"
    desc_file.write_text(json.dumps({"Name": "Generic Brain Study"}))

    with patch("code.datasets.verify_design.paths.data") as mock_paths:
        mock_paths.return_value = ds_dir
        success, reason = verify_dataset_design("ds000001")
        assert success is False
        assert reason == "design_missing_mindfulness_metadata"

def test_no_paired_scans(tmp_path):
    # Setup: mindfulness metadata but no paired scans
    ds_dir = tmp_path / "ds000001"
    ds_dir.mkdir(parents=True)
    desc_file = ds_dir / "dataset_description.json"
    desc_file.write_text(json.dumps({"Name": "Mindfulness Study"}))
    
    # Create one subject with only pre scan
    sub_dir = ds_dir / "sub-01"
    sub_dir.mkdir()
    ses_pre = sub_dir / "ses-pre"
    ses_pre.mkdir()
    (ses_pre / "func").mkdir()

    with patch("code.datasets.verify_design.paths.data") as mock_paths:
        mock_paths.return_value = ds_dir
        success, reason = verify_dataset_design("ds000001")
        assert success is False
        assert reason == "no_paired_pre_post_scans"

def test_successful_verification(tmp_path):
    # Setup: mindfulness metadata AND paired scans
    ds_dir = tmp_path / "ds000001"
    ds_dir.mkdir(parents=True)
    desc_file = ds_dir / "dataset_description.json"
    desc_file.write_text(json.dumps({"Name": "MBSR Mindfulness Study"}))
    
    # Create one subject with both pre and post
    sub_dir = ds_dir / "sub-01"
    sub_dir.mkdir()
    (sub_dir / "ses-pre" / "func").mkdir(parents=True)
    (sub_dir / "ses-post" / "func").mkdir(parents=True)

    with patch("code.datasets.verify_design.paths.data") as mock_paths:
        mock_paths.return_value = ds_dir
        # We also need to mock validate_schema since it depends on T017
        with patch("code.datasets.verify_design.validate_schema", return_value=True):
            success, reason = verify_dataset_design("ds000001")
            assert success is True
            assert reason == "verified"