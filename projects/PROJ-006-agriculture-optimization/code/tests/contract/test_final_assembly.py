"""
Contract tests for Final Dataset Assembly (T017d).
"""

import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.data.processing.final_assembly import (
    load_linkage_status,
    validate_final_dataset,
    assemble_final_dataset,
    main
)
from src.utils.io_helpers import FatalError


@pytest.fixture
def temp_workspace():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create necessary directories
        (tmpdir / "data" / "logs").mkdir(parents=True)
        (tmpdir / "data" / "processed").mkdir(parents=True)
        (tmpdir / "contracts").mkdir(parents=True)

        # Create a mock schema
        schema_content = """
        type: object
        properties:
          household_id:
            type: integer
          CSA_Index:
            type: number
          Stability_Score:
            type: number
        required:
          - household_id
          - CSA_Index
          - Stability_Score
        """
        (tmpdir / "contracts" / "dataset.schema.yaml").write_text(schema_content)

        # Create a mock feature engineered dataset
        feature_data = """household_id,CSA_Index,Stability_Score
        1,2.5,0.8
        2,3.0,0.9
        3,1.5,0.7
        """
        (tmpdir / "data" / "processed" / "feature_engineered_data.csv").write_text(feature_data)

        # Create a mock aggregated dataset
        agg_data = """household_id,CSA_Index,Stability_Score,village_id
        101,2.5,0.8,V1
        102,3.0,0.9,V1
        103,1.5,0.7,V2
        """
        (tmpdir / "data" / "processed" / "analysis_dataset_village_aggregated.csv").write_text(agg_data)

        yield tmpdir


def test_load_linkage_status_success(temp_workspace):
    """Test successful loading of linkage validation JSON."""
    linkage_data = {
        "linkage_percentage": 98.5,
        "total_valid_households": 1000,
        "triggered_aggregation": False,
        "exclusion_reason": "none"
    }
    linkage_path = temp_workspace / "data" / "logs" / "linkage_validation.json"
    linkage_path.write_text(json.dumps(linkage_data))

    result = load_linkage_status()
    assert result == linkage_data
    assert result["triggered_aggregation"] is False


def test_load_linkage_status_missing_file(temp_workspace):
    """Test that missing linkage file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_linkage_status()


def test_assemble_final_dataset_triggered(temp_workspace):
    """Test assembly when aggregation is triggered."""
    linkage_data = {
        "linkage_percentage": 90.0,
        "total_valid_households": 1000,
        "triggered_aggregation": True,
        "exclusion_reason": "low_linkage"
    }
    linkage_path = temp_workspace / "data" / "logs" / "linkage_validation.json"
    linkage_path.write_text(json.dumps(linkage_data))

    # Change to temp workspace
    original_cwd = os.getcwd()
    os.chdir(temp_workspace)

    try:
        # Mock validate_dataset_schema to avoid complex schema validation in unit test
        with patch("src.data.processing.final_assembly.validate_dataset_schema") as mock_validate:
            mock_validate.return_value = (True, [])
            assemble_final_dataset()

        # Check that the final dataset is the aggregated one
        assert (temp_workspace / "data" / "processed" / "analysis_dataset.csv").exists()
        final_content = (temp_workspace / "data" / "processed" / "analysis_dataset.csv").read_text()
        assert "village_id" in final_content  # Aggregated data has village_id
    finally:
        os.chdir(original_cwd)


def test_assemble_final_dataset_not_triggered(temp_workspace):
    """Test assembly when aggregation is NOT triggered."""
    linkage_data = {
        "linkage_percentage": 98.5,
        "total_valid_households": 1000,
        "triggered_aggregation": False,
        "exclusion_reason": "none"
    }
    linkage_path = temp_workspace / "data" / "logs" / "linkage_validation.json"
    linkage_path.write_text(json.dumps(linkage_data))

    original_cwd = os.getcwd()
    os.chdir(temp_workspace)

    try:
        with patch("src.data.processing.final_assembly.validate_dataset_schema") as mock_validate:
            mock_validate.return_value = (True, [])
            assemble_final_dataset()

        # Check that the final dataset is the feature engineered one
        assert (temp_workspace / "data" / "processed" / "analysis_dataset.csv").exists()
        final_content = (temp_workspace / "data" / "processed" / "analysis_dataset.csv").read_text()
        assert "village_id" not in final_content  # Feature engineered data doesn't have village_id in this mock
        assert "household_id,CSA_Index,Stability_Score" in final_content
    finally:
        os.chdir(original_cwd)


def test_assemble_final_dataset_missing_source(temp_workspace):
    """Test that missing source file raises FatalError."""
    linkage_data = {
        "linkage_percentage": 90.0,
        "total_valid_households": 1000,
        "triggered_aggregation": True,
        "exclusion_reason": "low_linkage"
    }
    linkage_path = temp_workspace / "data" / "logs" / "linkage_validation.json"
    linkage_path.write_text(json.dumps(linkage_data))

    # Remove the aggregated source file
    (temp_workspace / "data" / "processed" / "analysis_dataset_village_aggregated.csv").unlink()

    original_cwd = os.getcwd()
    os.chdir(temp_workspace)

    try:
        with patch("src.data.processing.final_assembly.validate_dataset_schema") as mock_validate:
            mock_validate.return_value = (True, [])
            with pytest.raises(FatalError, match="Aggregated dataset not found"):
                assemble_final_dataset()
    finally:
        os.chdir(original_cwd)


def test_main_integration_triggered(temp_workspace, caplog):
    """Test main() function with triggered aggregation."""
    linkage_data = {
        "linkage_percentage": 90.0,
        "total_valid_households": 1000,
        "triggered_aggregation": True,
        "exclusion_reason": "low_linkage"
    }
    linkage_path = temp_workspace / "data" / "logs" / "linkage_validation.json"
    linkage_path.write_text(json.dumps(linkage_data))

    original_cwd = os.getcwd()
    os.chdir(temp_workspace)

    try:
        with patch("src.data.processing.final_assembly.validate_dataset_schema") as mock_validate:
            mock_validate.return_value = (True, [])
            with patch("sys.argv", ["final_assembly.py", "--log-level", "INFO"]):
                main()

        assert (temp_workspace / "data" / "processed" / "analysis_dataset.csv").exists()
    finally:
        os.chdir(original_cwd)


def test_main_integration_not_triggered(temp_workspace, caplog):
    """Test main() function with non-triggered aggregation."""
    linkage_data = {
        "linkage_percentage": 98.5,
        "total_valid_households": 1000,
        "triggered_aggregation": False,
        "exclusion_reason": "none"
    }
    linkage_path = temp_workspace / "data" / "logs" / "linkage_validation.json"
    linkage_path.write_text(json.dumps(linkage_data))

    original_cwd = os.getcwd()
    os.chdir(temp_workspace)

    try:
        with patch("src.data.processing.final_assembly.validate_dataset_schema") as mock_validate:
            mock_validate.return_value = (True, [])
            with patch("sys.argv", ["final_assembly.py", "--log-level", "INFO"]):
                main()

        assert (temp_workspace / "data" / "processed" / "analysis_dataset.csv").exists()
    finally:
        os.chdir(original_cwd)
