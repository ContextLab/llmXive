import os
import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from main import aggregate_metrics_to_csv, load_exclusion_log, save_exclusion_log
from config import get_config_dict

@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary data directories."""
    processed_dir = tmp_path / "data" / "processed"
    logs_dir = tmp_path / "data" / "logs"
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path

def test_aggregate_metrics_creates_csvs(temp_dirs):
    """Test that aggregate_metrics_to_csv creates the required CSV files."""
    # Change to temp directory to simulate project root
    original_cwd = os.getcwd()
    os.chdir(temp_dirs)
    
    try:
        # Ensure data/processed exists
        (Path("data") / "processed").mkdir(parents=True, exist_ok=True)
        
        # Mock data
        structural_data = [
            {
                "subject_id": "sub-001",
                "global_efficiency": 0.45,
                "average_clustering": 0.32,
                "modularity": 0.65,
                "sparsity_ratio": 0.85,
                "exclusion_reason": None
            },
            {
                "subject_id": "sub-002",
                "global_efficiency": 0.48,
                "average_clustering": 0.30,
                "modularity": 0.62,
                "sparsity_ratio": 0.88,
                "exclusion_reason": None
            }
        ]
        
        dynamic_data = [
            {
                "subject_id": "sub-001",
                "mean_dwell_time": 12.5,
                "visited_states": 5,
                "total_windows": 100,
                "state_distribution": "0.2,0.2,0.2,0.2,0.2"
            },
            {
                "subject_id": "sub-002",
                "mean_dwell_time": 11.8,
                "visited_states": 4,
                "total_windows": 95,
                "state_distribution": "0.25,0.25,0.25,0.25,0.0"
            }
        ]
        
        config = get_config_dict()
        
        # Run aggregation
        aggregate_metrics_to_csv(structural_data, dynamic_data, config)
        
        # Verify files exist
        struct_path = Path("data/processed/structural_metrics.csv")
        dyn_path = Path("data/processed/dynamic_metrics.csv")
        
        assert struct_path.exists(), "structural_metrics.csv not created"
        assert dyn_path.exists(), "dynamic_metrics.csv not created"
        
        # Verify content
        df_struct = pd.read_csv(struct_path)
        df_dyn = pd.read_csv(dyn_path)
        
        assert len(df_struct) == 2
        assert len(df_dyn) == 2
        
        assert "subject_id" in df_struct.columns
        assert "global_efficiency" in df_struct.columns
        assert "mean_dwell_time" in df_dyn.columns
        
        # Check specific values
        assert df_struct.loc[0, "subject_id"] == "sub-001"
        assert df_struct.loc[0, "global_efficiency"] == 0.45
        
        print("Test passed: CSVs created with correct structure and data.")
        
    finally:
        os.chdir(original_cwd)

def test_empty_metrics_creates_header_only(temp_dirs):
    """Test that empty lists create CSVs with headers only."""
    original_cwd = os.getcwd()
    os.chdir(temp_dirs)
    
    try:
        (Path("data") / "processed").mkdir(parents=True, exist_ok=True)
        
        config = get_config_dict()
        aggregate_metrics_to_csv([], [], config)
        
        struct_path = Path("data/processed/structural_metrics.csv")
        dyn_path = Path("data/processed/dynamic_metrics.csv")
        
        assert struct_path.exists()
        assert dyn_path.exists()
        
        df_struct = pd.read_csv(struct_path)
        df_dyn = pd.read_csv(dyn_path)
        
        assert len(df_struct) == 0
        assert len(df_dyn) == 0
        
        # Check headers exist
        assert "subject_id" in df_struct.columns
        assert "mean_dwell_time" in df_dyn.columns
        
        print("Test passed: Empty CSVs created with headers.")
        
    finally:
        os.chdir(original_cwd)