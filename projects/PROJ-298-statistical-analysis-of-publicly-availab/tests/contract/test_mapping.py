"""
Contract Test for T015: Tag-to-Repository Mapping

Validates that the output of code/analysis/mapping.py adheres to the expected schema
and correctly logs unmapped tags.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import the module
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from analysis.mapping import (
    load_json_safe,
    validate_external_metrics,
    select_best_candidate,
    map_tag_to_repos,
    run_mapping_pipeline,
    OUTPUT_MAPPING_FILE,
    OUTPUT_UNMAPPED_LOG
)


def test_load_json_safe_missing_file():
    """Test loading a non-existent file returns None."""
    result = load_json_safe(Path("/nonexistent/file.json"))
    assert result is None


def test_load_json_safe_invalid_json():
    """Test loading invalid JSON returns None."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{ invalid json }")
        temp_path = Path(f.name)

    try:
        result = load_json_safe(temp_path)
        assert result is None
    finally:
        os.unlink(temp_path)


def test_validate_external_metrics_valid():
    """Test validation of a correctly structured input."""
    data = {"metrics": [{"tag": "python", "github_candidates": []}]}
    assert validate_external_metrics(data, schema=None) is True


def test_validate_external_metrics_missing_key():
    """Test validation fails if 'metrics' key is missing."""
    data = {"other_key": []}
    assert validate_external_metrics(data, schema=None) is False


def test_validate_external_metrics_metrics_not_list():
    """Test validation fails if 'metrics' is not a list."""
    data = {"metrics": "not a list"}
    assert validate_external_metrics(data, schema=None) is False


def test_select_best_candidate_exact_match():
    """Test that exact match is preferred over non-exact."""
    candidates = [
        {"name": "pkg", "is_exact_match": False, "downloads": 10000},
        {"name": "pkg", "is_exact_match": True, "downloads": 100}
    ]
    best = select_best_candidate(candidates)
    assert best["is_exact_match"] is True


def test_select_best_candidate_popularity():
    """Test that higher popularity is preferred if no exact match."""
    candidates = [
        {"name": "pkg", "is_exact_match": False, "downloads": 100},
        {"name": "pkg", "is_exact_match": False, "downloads": 10000}
    ]
    best = select_best_candidate(candidates)
    assert best["downloads"] == 10000


def test_select_best_candidate_empty():
    """Test selecting from empty list returns None."""
    assert select_best_candidate([]) is None


def test_map_tag_to_repos_success():
    """Test mapping a tag with valid candidates."""
    tag_data = {
        "github_candidates": [{"full_name": "test/repo", "stars": 100, "url": "http://test", "is_exact_match": True}],
        "npm_candidates": []
    }
    result = map_tag_to_repos("test-tag", tag_data)
    assert result["tag"] == "test-tag"
    assert result["github_repo"] is not None
    assert result["github_repo"]["full_name"] == "test/repo"
    assert result["mapping_status"] == "mapped"


def test_map_tag_to_repos_unmapped():
    """Test mapping a tag with no candidates."""
    tag_data = {
        "github_candidates": [],
        "npm_candidates": []
    }
    result = map_tag_to_repos("test-tag", tag_data)
    assert result["mapping_status"] == "unmapped"
    assert result["github_repo"] is None
    assert result["npm_package"] is None


def test_run_mapping_pipeline_missing_input_creates_empty_outputs(tmp_path):
    """
    Test that if input file is missing, the pipeline creates empty output files
    and exits successfully (returning True).
    """
    # Mock the global paths to use tmp_path
    with patch('analysis.mapping.DATA_PROCESSED_DIR', tmp_path), \
         patch('analysis.mapping.INPUT_FILE', tmp_path / "external_metrics.json"), \
         patch('analysis.mapping.OUTPUT_MAPPING_FILE', tmp_path / "tag_mappings.json"), \
         patch('analysis.mapping.OUTPUT_UNMAPPED_LOG', tmp_path / "unmapped_tags.log"):

        # Input file does not exist
        assert not (tmp_path / "external_metrics.json").exists()

        result = run_mapping_pipeline()

        assert result is True
        assert (tmp_path / "tag_mappings.json").exists()
        assert (tmp_path / "unmapped_tags.log").exists()

        with open(tmp_path / "tag_mappings.json") as f:
            data = json.load(f)
            assert data == []


def test_run_mapping_pipeline_empty_metrics_creates_empty_outputs(tmp_path):
    """
    Test that if input file exists but has empty metrics list,
    the pipeline creates empty output files and exits successfully.
    """
    input_file = tmp_path / "external_metrics.json"
    with open(input_file, 'w') as f:
        json.dump({"metrics": []}, f)

    with patch('analysis.mapping.DATA_PROCESSED_DIR', tmp_path), \
         patch('analysis.mapping.INPUT_FILE', input_file), \
         patch('analysis.mapping.OUTPUT_MAPPING_FILE', tmp_path / "tag_mappings.json"), \
         patch('analysis.mapping.OUTPUT_UNMAPPED_LOG', tmp_path / "unmapped_tags.log"):

        result = run_mapping_pipeline()

        assert result is True
        assert (tmp_path / "tag_mappings.json").exists()
        assert (tmp_path / "unmapped_tags.log").exists()


def test_run_mapping_pipeline_full_flow(tmp_path):
    """
    Test the full mapping flow with valid data.
    """
    input_file = tmp_path / "external_metrics.json"
    test_data = {
        "metrics": [
            {
                "tag": "python",
                "github_candidates": [{"full_name": "psf/requests", "stars": 5000, "url": "http://req", "is_exact_match": True}],
                "npm_candidates": []
            },
            {
                "tag": "unknown-tag",
                "github_candidates": [],
                "npm_candidates": []
            }
        ]
    }
    with open(input_file, 'w') as f:
        json.dump(test_data, f)

    with patch('analysis.mapping.DATA_PROCESSED_DIR', tmp_path), \
         patch('analysis.mapping.INPUT_FILE', input_file), \
         patch('analysis.mapping.OUTPUT_MAPPING_FILE', tmp_path / "tag_mappings.json"), \
         patch('analysis.mapping.OUTPUT_UNMAPPED_LOG', tmp_path / "unmapped_tags.log"):

        result = run_mapping_pipeline()

        assert result is True

        # Check mapping file
        with open(tmp_path / "tag_mappings.json") as f:
            mappings = json.load(f)
            assert len(mappings) == 2
            assert mappings[0]["tag"] == "python"
            assert mappings[0]["mapping_status"] == "mapped"
            assert mappings[1]["tag"] == "unknown-tag"
            assert mappings[1]["mapping_status"] == "unmapped"

        # Check unmapped log
        with open(tmp_path / "unmapped_tags.log") as f:
            lines = f.readlines()
            assert len(lines) == 1
            log_entry = json.loads(lines[0])
            assert log_entry["tag"] == "unknown-tag"