import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analyze import load_training_run, extract_scalars, verify_extraction, aggregate_training_runs

@pytest.fixture
def sample_training_run():
    """Create a sample training run dictionary."""
    return {
        "id": "test_run_001",
        "loss_type": "ce",
        "beta": 0.5,
        "node_count": 100,
        "steps_to_convergence": 50,
        "final_accuracy": 0.95,
        "max_loss": 0.1,
        "convergence_status": "converged",
        "trajectory": [
            {"loss": 0.5, "accuracy": 0.6},
            {"loss": 0.3, "accuracy": 0.8},
            {"loss": 0.1, "accuracy": 0.95}
        ]
    }

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory with sample training run files."""
    runs = [
        {
            "id": "run_ce_001",
            "loss_type": "ce",
            "beta": 0.0,
            "node_count": 100,
            "steps_to_convergence": 45,
            "final_accuracy": 0.92,
            "max_loss": 0.15,
            "convergence_status": "converged",
            "trajectory": [{"loss": 0.5, "accuracy": 0.6}]
        },
        {
            "id": "run_infonce_001",
            "loss_type": "infonce",
            "beta": 0.0,
            "node_count": 100,
            "steps_to_convergence": 60,
            "final_accuracy": 0.90,
            "max_loss": 0.2,
            "convergence_status": "censored",
            "trajectory": [{"loss": 0.6, "accuracy": 0.55}]
        },
        {
            "id": "run_ce_002",
            "loss_type": "ce",
            "beta": 0.5,
            "node_count": 100,
            "steps_to_convergence": 30,
            "final_accuracy": 0.94,
            "max_loss": 0.12,
            "convergence_status": "converged",
            "trajectory": [{"loss": 0.4, "accuracy": 0.7}]
        }
    ]
    
    output_dir = tmp_path / "trajectories"
    output_dir.mkdir()
    
    for i, run in enumerate(runs):
        file_path = output_dir / f"training_run_{i}.json"
        with open(file_path, 'w') as f:
            json.dump(run, f)
            
    return str(output_dir)

def test_load_training_run(sample_training_run, tmp_path):
    """Test loading a training run from a JSON file."""
    file_path = tmp_path / "test_run.json"
    with open(file_path, 'w') as f:
        json.dump(sample_training_run, f)
        
    loaded = load_training_run(str(file_path))
    assert loaded["id"] == sample_training_run["id"]
    assert loaded["loss_type"] == sample_training_run["loss_type"]
    assert len(loaded["trajectory"]) == len(sample_training_run["trajectory"])

def test_extract_scalars(sample_training_run):
    """Test extraction of scalar fields from training run data."""
    scalars = extract_scalars(sample_training_run)
    
    # Check that all expected scalar fields are present
    expected_fields = ["run_id", "loss_type", "beta", "node_count", 
                     "steps_to_convergence", "final_accuracy", "max_loss", 
                     "convergence_status"]
    for field in expected_fields:
        assert field in scalars
        
    # Check that trajectory is NOT included
    assert "trajectory" not in scalars
    
    # Check values
    assert scalars["run_id"] == sample_training_run["id"]
    assert scalars["loss_type"] == sample_training_run["loss_type"]
    assert scalars["beta"] == sample_training_run["beta"]
    assert scalars["steps_to_convergence"] == sample_training_run["steps_to_convergence"]

def test_verify_extraction(sample_training_run):
    """Test verification that extracted scalars match original data."""
    scalars = extract_scalars(sample_training_run)
    assert verify_extraction(sample_training_run, scalars) is True
    
    # Test with modified data (should fail)
    modified_scalars = scalars.copy()
    modified_scalars["steps_to_convergence"] = 999
    assert verify_extraction(sample_training_run, modified_scalars) is False

def test_aggregate_training_runs(temp_data_dir, tmp_path):
    """Test aggregation of multiple training runs into a DataFrame."""
    output_path = str(tmp_path / "convergence_logs.csv")
    df = aggregate_training_runs(temp_data_dir, output_path)
    
    # Check DataFrame structure
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3  # We created 3 runs
    
    # Check columns
    expected_columns = ["run_id", "loss_type", "beta", "node_count", 
                      "steps_to_convergence", "final_accuracy", "max_loss", 
                      "convergence_status"]
    for col in expected_columns:
        assert col in df.columns
        
    # Check that trajectory is NOT in the DataFrame
    assert "trajectory" not in df.columns
    
    # Check values
    assert df["loss_type"].nunique() == 2  # ce and infonce
    assert df["beta"].nunique() == 2  # 0.0 and 0.5
    
    # Check file was created
    assert os.path.exists(output_path)
    
    # Verify CSV content matches DataFrame
    df_from_csv = pd.read_csv(output_path)
    assert len(df_from_csv) == len(df)

def test_aggregate_with_no_files(tmp_path):
    """Test aggregation when no matching files exist."""
    empty_dir = tmp_path / "empty_trajectories"
    empty_dir.mkdir()
    
    output_path = str(tmp_path / "output.csv")
    
    with pytest.raises(FileNotFoundError):
        aggregate_training_runs(str(empty_dir), output_path)

def test_aggregate_preserves_scalar_values(temp_data_dir, tmp_path):
    """Test that aggregated values exactly match source JSON files."""
    output_path = str(tmp_path / "convergence_logs.csv")
    df = aggregate_training_runs(temp_data_dir, output_path)
    
    # Load original files to verify
    files = list(Path(temp_data_dir).glob("training_run_*.json"))
    for i, file_path in enumerate(files):
        with open(file_path, 'r') as f:
            original = json.load(f)
            
        # Find corresponding row in DataFrame
        row = df[df["run_id"] == original["id"]].iloc[0]
        
        # Verify scalar fields match
        assert row["beta"] == original["beta"]
        assert row["steps_to_convergence"] == original["steps_to_convergence"]
        assert row["final_accuracy"] == original["final_accuracy"]
        assert row["max_loss"] == original["max_loss"]
        assert row["convergence_status"] == original["convergence_status"]
