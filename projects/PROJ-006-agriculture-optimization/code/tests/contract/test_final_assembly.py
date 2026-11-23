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

# Import the module under test
from src.data.processing.final_assembly import (
    load_linkage_status,
    validate_final_dataset,
    assemble_final_dataset,
    main
)
from src.utils.io_helpers import FatalError


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        data_dir = base / "data" / "processed"
        logs_dir = base / "data" / "logs"
        data_dir.mkdir(parents=True)
        logs_dir.mkdir(parents=True)
        yield {
            "base": base,
            "logs_dir": logs_dir,
            "data_dir": data_dir,
            "linkage_file": logs_dir / "linkage_validation.json",
            "aggregated_file": data_dir / "analysis_dataset_village_aggregated.csv",
            "engineered_file": data_dir / "feature_engineered_data.csv",
            "output_file": data_dir / "analysis_dataset.csv",
            "schema_file": base / "contracts" / "dataset.schema.yaml"
        }


def test_load_linkage_status_success(temp_workspace):
    """Test successful loading of linkage status."""
    # Create a valid linkage JSON
    linkage_data = {
        "linkage_percentage": 98.5,
        "total_valid_households": 1200,
        "triggered_aggregation": False,
        "exclusion_reason": "none"
    }
    with open(temp_workspace["linkage_file"], "w") as f:
        json.dump(linkage_data, f)

    result = load_linkage_status(temp_workspace["linkage_file"])
    assert result == linkage_data
    assert result["triggered_aggregation"] is False


def test_load_linkage_status_missing_file(temp_workspace):
    """Test loading missing linkage file raises error."""
    with pytest.raises(FileNotFoundError):
        load_linkage_status(temp_workspace["linkage_file"])


def test_assemble_final_dataset_triggered(temp_workspace):
    """Test assembly when aggregation is triggered."""
    # Create linkage status with triggered_aggregation = True
    linkage_data = {
        "linkage_percentage": 90.0,
        "total_valid_households": 250,
        "triggered_aggregation": True,
        "exclusion_reason": "low_linkage"
    }
    with open(temp_workspace["linkage_file"], "w") as f:
        json.dump(linkage_data, f)

    # Create dummy aggregated dataset
    aggregated_content = "household_id,CSA_Index,Stability_Score\n1,3,0.8\n2,4,0.9\n"
    with open(temp_workspace["aggregated_file"], "w") as f:
        f.write(aggregated_content)

    # Create dummy engineered dataset (should NOT be used)
    engineered_content = "household_id,CSA_Index,Stability_Score\n99,0,0.0\n"
    with open(temp_workspace["engineered_file"], "w") as f:
        f.write(engineered_content)

    # Assemble
    assemble_final_dataset(
        linkage_data,
        temp_workspace["aggregated_file"],
        temp_workspace["engineered_file"],
        temp_workspace["output_file"]
    )

    # Verify output matches aggregated file
    assert temp_workspace["output_file"].exists()
    with open(temp_workspace["output_file"], "r") as f:
        content = f.read()
    assert content == aggregated_content


def test_assemble_final_dataset_not_triggered(temp_workspace):
    """Test assembly when aggregation is NOT triggered."""
    # Create linkage status with triggered_aggregation = False
    linkage_data = {
        "linkage_percentage": 99.0,
        "total_valid_households": 1500,
        "triggered_aggregation": False,
        "exclusion_reason": "none"
    }
    with open(temp_workspace["linkage_file"], "w") as f:
        json.dump(linkage_data, f)

    # Create dummy aggregated dataset (should NOT be used)
    aggregated_content = "household_id,CSA_Index,Stability_Score\n1,3,0.8\n"
    with open(temp_workspace["aggregated_file"], "w") as f:
        f.write(aggregated_content)

    # Create dummy engineered dataset
    engineered_content = "household_id,CSA_Index,Stability_Score\n10,5,0.95\n11,6,0.92\n"
    with open(temp_workspace["engineered_file"], "w") as f:
        f.write(engineered_content)

    # Assemble
    assemble_final_dataset(
        linkage_data,
        temp_workspace["aggregated_file"],
        temp_workspace["engineered_file"],
        temp_workspace["output_file"]
    )

    # Verify output matches engineered file
    assert temp_workspace["output_file"].exists()
    with open(temp_workspace["output_file"], "r") as f:
        content = f.read()
    assert content == engineered_content


def test_assemble_final_dataset_missing_source(temp_workspace):
    """Test assembly when source file is missing."""
    linkage_data = {
        "linkage_percentage": 90.0,
        "total_valid_households": 250,
        "triggered_aggregation": True,
        "exclusion_reason": "low_linkage"
    }
    with open(temp_workspace["linkage_file"], "w") as f:
        json.dump(linkage_data, f)

    # Do NOT create the aggregated file

    with pytest.raises(FileNotFoundError):
        assemble_final_dataset(
            linkage_data,
            temp_workspace["aggregated_file"],
            temp_workspace["engineered_file"],
            temp_workspace["output_file"]
        )


def test_main_integration_triggered(temp_workspace):
    """Test main function with triggered aggregation."""
    # Setup files
    linkage_data = {
        "linkage_percentage": 90.0,
        "total_valid_households": 250,
        "triggered_aggregation": True,
        "exclusion_reason": "low_linkage"
    }
    with open(temp_workspace["linkage_file"], "w") as f:
        json.dump(linkage_data, f)

    # Create a valid CSV for aggregated data
    # Note: In a real test, we would need a valid schema file.
    # For this unit test, we mock the validation to pass.
    aggregated_content = "household_id,CSA_Index,Stability_Score\n1,3,0.8\n2,4,0.9\n"
    with open(temp_workspace["aggregated_file"], "w") as f:
        f.write(aggregated_content)

    # Mock the validation function to avoid schema dependency in unit test
    with patch("src.data.processing.final_assembly.validate_final_dataset") as mock_validate:
        mock_validate.return_value = True

        args = [
            "--linkage-status", str(temp_workspace["linkage_file"]),
            "--aggregated-dataset", str(temp_workspace["aggregated_file"]),
            "--engineered-dataset", str(temp_workspace["engineered_file"]),
            "--output", str(temp_workspace["output_file"]),
            "--log-level", "WARNING"
        ]

        with patch("sys.argv", ["final_assembly"] + args):
            result = main()

        assert result == 0
        assert temp_workspace["output_file"].exists()


def test_main_integration_not_triggered(temp_workspace):
    """Test main function with no aggregation triggered."""
    # Setup files
    linkage_data = {
        "linkage_percentage": 99.0,
        "total_valid_households": 1500,
        "triggered_aggregation": False,
        "exclusion_reason": "none"
    }
    with open(temp_workspace["linkage_file"], "w") as f:
        json.dump(linkage_data, f)

    # Create a valid CSV for engineered data
    engineered_content = "household_id,CSA_Index,Stability_Score\n10,5,0.95\n"
    with open(temp_workspace["engineered_file"], "w") as f:
        f.write(engineered_content)

    # Mock validation
    with patch("src.data.processing.final_assembly.validate_final_dataset") as mock_validate:
        mock_validate.return_value = True

        args = [
            "--linkage-status", str(temp_workspace["linkage_file"]),
            "--aggregated-dataset", str(temp_workspace["aggregated_file"]),
            "--engineered-dataset", str(temp_workspace["engineered_file"]),
            "--output", str(temp_workspace["output_file"]),
            "--log-level", "WARNING"
        ]

        with patch("sys.argv", ["final_assembly"] + args):
            result = main()

        assert result == 0
        assert temp_workspace["output_file"].exists()