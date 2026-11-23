import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
from code.data.split import main as split_main, load_processed_data
from llmxive_toolkit import paths

def test_split_files_created(tmp_path, monkeypatch):
    """Verify that split.py creates both CSV and Parquet files for train and test."""
    # Mock the data directory to use a temporary path
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    
    # Create a dummy processed dataset
    df = pd.DataFrame({
        "smiles": ["C", "CC", "CCC", "CCCC", "CCCCC", "CCCCCC", "CCCCCCC", "CCCCCCCC"],
        "permeability": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7],
        "polymer_type": ["A", "A", "A", "A", "B", "B", "B", "B"]
    })
    df.to_parquet(processed_dir / "processed_data.parquet")
    df.to_csv(processed_dir / "processed_data.csv", index=False)

    # Monkeypatch paths.data to return our tmp_path
    def mock_paths_data(*args):
        if args[0] == "processed":
            return processed_dir
        return Path("data") / args[0]
    
    monkeypatch.setattr("code.data.split.paths.data", mock_paths_data)

    # Run the split main
    exit_code = split_main()
    assert exit_code == 0

    # Check for all 4 split files + metadata
    assert (processed_dir / "train.csv").exists()
    assert (processed_dir / "train.parquet").exists()
    assert (processed_dir / "test.csv").exists()
    assert (processed_dir / "test.parquet").exists()
    assert (processed_dir / "split_metadata.json").exists()

    # Verify metadata content
    with open(processed_dir / "split_metadata.json", "r") as f:
        meta = json.load(f)
        assert meta["split_strategy"] == "stratified"
        assert meta["stratify_column"] == "polymer_type"
        assert meta["train_size"] == 6
        assert meta["test_size"] == 2

def test_small_dataset_leave_one_out(tmp_path, monkeypatch):
    """Verify leave-one-out split for datasets with <= 5 rows."""
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    
    # 4 rows dataset
    df = pd.DataFrame({
        "smiles": ["C", "CC", "CCC", "CCCC"],
        "permeability": [1.0, 1.1, 1.2, 1.3],
        "polymer_type": ["A", "A", "B", "B"]
    })
    df.to_parquet(processed_dir / "processed_data.parquet")

    def mock_paths_data(*args):
        if args[0] == "processed":
            return processed_dir
        return Path("data") / args[0]
    
    monkeypatch.setattr("code.data.split.paths.data", mock_paths_data)

    exit_code = split_main()
    assert exit_code == 0

    with open(processed_dir / "split_metadata.json", "r") as f:
        meta = json.load(f)
        assert meta["split_strategy"] == "leave_one_out"
        assert meta["train_size"] == 3
        assert meta["test_size"] == 1

def test_quantile_stratification(tmp_path, monkeypatch):
    """Verify stratification by target quantiles when polymer_type is missing."""
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    
    # No polymer_type, but enough rows for quantiles
    df = pd.DataFrame({
        "smiles": [f"M{i}" for i in range(20)],
        "permeability": np.linspace(0, 10, 20)
    })
    df.to_parquet(processed_dir / "processed_data.parquet")

    def mock_paths_data(*args):
        if args[0] == "processed":
            return processed_dir
        return Path("data") / args[0]
    
    monkeypatch.setattr("code.data.split.paths.data", mock_paths_data)

    exit_code = split_main()
    assert exit_code == 0

    with open(processed_dir / "split_metadata.json", "r") as f:
        meta = json.load(f)
        assert meta["split_strategy"] == "stratified"
        assert meta["stratify_column"] == "_strat_bins"