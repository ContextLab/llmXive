import pandas as pd
import pytest
from pathlib import Path
import tempfile
import json

# Mock the config to avoid needing a full project setup for the unit test
import sys
from unittest.mock import patch, MagicMock

# We need to mock get_project_root to return a temp directory
@pytest.fixture
def temp_project_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create necessary subdirectories
        (tmpdir / "data" / "processed").mkdir(parents=True)
        (tmpdir / "data" / "raw").mkdir(parents=True)
        (tmpdir / "data" / "results").mkdir(parents=True)
        (tmpdir / "specs").mkdir(parents=True)
        # Create a minimal config if needed
        config_path = tmpdir / "config.yaml"
        config_path.write_text("THRESHOLD_DATA_SCARCITY: 120\n")
        yield tmpdir

@pytest.fixture
def sample_residuals(temp_project_dir):
    residuals_path = temp_project_dir / "data" / "processed" / "residuals.parquet"
    data = {
        "sample_id": ["s1", "s2", "s3"],
        "error_ml_dft": [0.1, -0.2, 0.05],
        "dft_barrier": [10.0, 15.0, 20.0],
        "ligand_class": ["Group 13", "Conventional", "Group 13"],
        "metal_center": ["Pd", "Ni", "Cu"]
    }
    df = pd.DataFrame(data)
    df.to_parquet(residuals_path)
    return residuals_path

@pytest.fixture
def sample_graphs(temp_project_dir):
    graphs_path = temp_project_dir / "data" / "processed" / "graphs.parquet"
    data = {
        "sample_id": ["s1", "s2", "s3", "s4"],
        "ligand_class": ["Group 13", "Conventional", "Group 13", "Conventional"],
        "metal_center": ["Pd", "Ni", "Cu", "Pd"],
        "extra_attr": [100, 200, 300, 400]
    }
    df = pd.DataFrame(data)
    df.to_parquet(graphs_path)
    return graphs_path

def test_aggregate_predictions_happy_path(temp_project_dir, sample_residuals, sample_graphs):
    from src.data.generate_final_artifacts import aggregate_predictions
    
    output_path = temp_project_dir / "data" / "processed" / "predictions.parquet"
    
    aggregate_predictions(sample_residuals, sample_graphs, output_path)
    
    assert output_path.exists(), "Output file was not created"
    
    result_df = pd.read_parquet(output_path)
    
    # Check columns
    assert "sample_id" in result_df.columns
    assert "error_ml_dft" in result_df.columns
    assert "dft_barrier" in result_df.columns
    assert "predicted_barrier" in result_df.columns
    
    # Check calculation: predicted = dft + error
    expected_predicted = result_df["dft_barrier"] + result_df["error_ml_dft"]
    pd.testing.assert_series_equal(result_df["predicted_barrier"], expected_predicted)
    
    # Check row count (should match residuals as it's the primary source)
    assert len(result_df) == 3

def test_aggregate_predictions_missing_graphs(temp_project_dir, sample_residuals):
    from src.data.generate_final_artifacts import aggregate_predictions
    
    # Use a non-existent graphs path
    non_existent_graphs = temp_project_dir / "data" / "processed" / "non_existent.parquet"
    output_path = temp_project_dir / "data" / "processed" / "predictions_no_graphs.parquet"
    
    aggregate_predictions(sample_residuals, non_existent_graphs, output_path)
    
    assert output_path.exists()
    result_df = pd.read_parquet(output_path)
    assert len(result_df) == 3

def test_aggregate_predictions_missing_dft_column(temp_project_dir, sample_residuals, sample_graphs):
    from src.data.generate_final_artifacts import aggregate_predictions
    
    # Modify residuals to remove dft_barrier
    temp_residuals = temp_project_dir / "data" / "processed" / "residuals_no_dft.parquet"
    data = {
        "sample_id": ["s1", "s2"],
        "error_ml_dft": [0.1, -0.2],
        "ligand_class": ["A", "B"]
    }
    pd.DataFrame(data).to_parquet(temp_residuals)
    
    output_path = temp_project_dir / "data" / "processed" / "predictions_no_dft.parquet"
    
    aggregate_predictions(temp_residuals, sample_graphs, output_path)
    
    result_df = pd.read_parquet(output_path)
    # Should have NaN for predicted_barrier if dft is missing
    assert result_df["predicted_barrier"].isna().all()