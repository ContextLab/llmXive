"""
Contract tests for T017d: Final Dataset Validation and Assembly.
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

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
    tmpdir = tempfile.mkdtemp()
    base = Path(tmpdir)
    
    # Create required subdirectories
    (base / "data" / "logs").mkdir(parents=True)
    (base / "data" / "processed").mkdir(parents=True)
    (base / "contracts").mkdir(parents=True)
    
    yield base
    
    shutil.rmtree(tmpdir)


def test_load_linkage_status_success(temp_workspace):
    """Test loading a valid linkage validation JSON."""
    log_path = temp_workspace / "data" / "logs" / "linkage_validation.json"
    data = {
        "linkage_percentage": 98.5,
        "total_valid_households": 500,
        "triggered_aggregation": False,
        "exclusion_reason": None
    }
    with open(log_path, 'w') as f:
        json.dump(data, f)
    
    result = load_linkage_status(log_path)
    assert result["triggered_aggregation"] is False
    assert result["linkage_percentage"] == 98.5


def test_load_linkage_status_missing_file(temp_workspace):
    """Test loading from a non-existent file raises FileNotFoundError."""
    log_path = temp_workspace / "data" / "logs" / "missing.json"
    with pytest.raises(FileNotFoundError):
        load_linkage_status(log_path)


def test_assemble_final_dataset_triggered(temp_workspace):
    """Test assembly when aggregation is triggered."""
    agg_path = temp_workspace / "data" / "processed" / "analysis_dataset_village_aggregated.csv"
    fe_path = temp_workspace / "data" / "processed" / "feature_engineered_data.csv"
    out_path = temp_workspace / "data" / "processed" / "analysis_dataset.csv"
    
    # Create dummy source files
    df_agg = pd.DataFrame({"village_id": [1, 2], "CSA_Index": [0.5, 0.6]})
    df_fe = pd.DataFrame({"household_id": [101], "CSA_Index": [0.5]})
    
    df_agg.to_csv(agg_path, index=False)
    df_fe.to_csv(fe_path, index=False)
    
    # Mock the linkage data to trigger aggregation
    with patch('src.data.processing.final_assembly.LINKAGE_VALIDATION_PATH', 
               temp_workspace / "data" / "logs" / "linkage_validation.json"):
        with patch('src.data.processing.final_assembly.AGGREGATED_DATASET_PATH', agg_path):
            with patch('src.data.processing.final_assembly.FEATURE_ENGINEERED_PATH', fe_path):
                with patch('src.data.processing.final_assembly.FINAL_DATASET_PATH', out_path):
                    # Simulate the logic directly
                    assemble_final_dataset(True, agg_path, fe_path, out_path)
                    
                    assert out_path.exists()
                    final_df = pd.read_csv(out_path)
                    assert len(final_df) == 2  # From aggregated
                    assert "village_id" in final_df.columns


def test_assemble_final_dataset_not_triggered(temp_workspace):
    """Test assembly when aggregation is NOT triggered."""
    agg_path = temp_workspace / "data" / "processed" / "analysis_dataset_village_aggregated.csv"
    fe_path = temp_workspace / "data" / "processed" / "feature_engineered_data.csv"
    out_path = temp_workspace / "data" / "processed" / "analysis_dataset.csv"
    
    # Create dummy source files
    df_agg = pd.DataFrame({"village_id": [1, 2], "CSA_Index": [0.5, 0.6]})
    df_fe = pd.DataFrame({"household_id": [101], "CSA_Index": [0.5]})
    
    df_agg.to_csv(agg_path, index=False)
    df_fe.to_csv(fe_path, index=False)
    
    # Simulate the logic directly
    assemble_final_dataset(False, agg_path, fe_path, out_path)
    
    assert out_path.exists()
    final_df = pd.read_csv(out_path)
    assert len(final_df) == 1  # From feature engineered
    assert "household_id" in final_df.columns


def test_assemble_final_dataset_missing_source(temp_workspace):
    """Test assembly fails if the required source file is missing."""
    agg_path = temp_workspace / "data" / "processed" / "analysis_dataset_village_aggregated.csv"
    fe_path = temp_workspace / "data" / "processed" / "feature_engineered_data.csv"
    out_path = temp_workspace / "data" / "processed" / "analysis_dataset.csv"
    
    # Only create aggregated, not feature engineered
    df_agg = pd.DataFrame({"village_id": [1], "CSA_Index": [0.5]})
    df_agg.to_csv(agg_path, index=False)
    
    with pytest.raises(FileNotFoundError):
        assemble_final_dataset(False, agg_path, fe_path, out_path)


def test_main_integration_triggered(temp_workspace):
    """Integration test for main() with aggregation triggered."""
    # Setup paths
    log_path = temp_workspace / "data" / "logs" / "linkage_validation.json"
    agg_path = temp_workspace / "data" / "processed" / "analysis_dataset_village_aggregated.csv"
    fe_path = temp_workspace / "data" / "processed" / "feature_engineered_data.csv"
    out_path = temp_workspace / "data" / "processed" / "analysis_dataset.csv"
    
    # Create linkage data
    with open(log_path, 'w') as f:
        json.dump({"triggered_aggregation": True}, f)
    
    # Create source data
    pd.DataFrame({"village_id": [1, 2], "CSA_Index": [0.5, 0.6]}).to_csv(agg_path, index=False)
    pd.DataFrame({"household_id": [101]}).to_csv(fe_path, index=False)
    
    # Mock paths
    with patch('src.data.processing.final_assembly.LINKAGE_VALIDATION_PATH', log_path):
        with patch('src.data.processing.final_assembly.AGGREGATED_DATASET_PATH', agg_path):
            with patch('src.data.processing.final_assembly.FEATURE_ENGINEERED_PATH', fe_path):
                with patch('src.data.processing.final_assembly.FINAL_DATASET_PATH', out_path):
                    with patch('src.data.processing.final_assembly.SCHEMA_PATH', temp_workspace / "contracts" / "nonexistent.yaml"):
                        # Run main
                        exit_code = main()
                        assert exit_code == 0
                        assert out_path.exists()
                        assert len(pd.read_csv(out_path)) == 2


def test_main_integration_not_triggered(temp_workspace):
    """Integration test for main() with aggregation NOT triggered."""
    # Setup paths
    log_path = temp_workspace / "data" / "logs" / "linkage_validation.json"
    agg_path = temp_workspace / "data" / "processed" / "analysis_dataset_village_aggregated.csv"
    fe_path = temp_workspace / "data" / "processed" / "feature_engineered_data.csv"
    out_path = temp_workspace / "data" / "processed" / "analysis_dataset.csv"
    
    # Create linkage data
    with open(log_path, 'w') as f:
        json.dump({"triggered_aggregation": False}, f)
    
    # Create source data
    pd.DataFrame({"village_id": [1, 2]}).to_csv(agg_path, index=False)
    pd.DataFrame({"household_id": [101, 102], "CSA_Index": [0.5, 0.6]}).to_csv(fe_path, index=False)
    
    # Mock paths
    with patch('src.data.processing.final_assembly.LINKAGE_VALIDATION_PATH', log_path):
        with patch('src.data.processing.final_assembly.AGGREGATED_DATASET_PATH', agg_path):
            with patch('src.data.processing.final_assembly.FEATURE_ENGINEERED_PATH', fe_path):
                with patch('src.data.processing.final_assembly.FINAL_DATASET_PATH', out_path):
                    with patch('src.data.processing.final_assembly.SCHEMA_PATH', temp_workspace / "contracts" / "nonexistent.yaml"):
                        # Run main
                        exit_code = main()
                        assert exit_code == 0
                        assert out_path.exists()
                        assert len(pd.read_csv(out_path)) == 2