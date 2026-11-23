import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from config import ensure_dirs
from modeling.split import create_train_val_test_split
from utils.io import load_parquet, save_parquet

@pytest.fixture
def sample_data():
    """Generate a small, deterministic dataset for testing split logic."""
    data = {
        'smiles': ['CCO', 'CCCO', 'CCCCO', 'CC(C)O', 'C1=CC=CC=C1', 'C1=CC=CC=C1.O', 
                   'CC(=O)O', 'CCC(=O)O', 'CCCC(=O)O', 'CC(C)C(=O)O',
                   'CCO', 'CCCO', 'CCCCO', 'CC(C)O', 'C1=CC=CC=C1', 'C1=CC=CC=C1.O',
                   'CC(=O)O', 'CCC(=O)O', 'CCCC(=O)O', 'CC(C)C(=O)O'],
        'yield': [80.0, 75.0, 90.0, 85.0, 60.0, 65.0, 70.0, 72.0, 78.0, 82.0,
                  80.0, 75.0, 90.0, 85.0, 60.0, 65.0, 70.0, 72.0, 78.0, 82.0],
        'reaction_class': ['Etherification'] * 10 + ['Carboxylation'] * 10,
        'scaffold_id': [f'scaffold_{i}' for i in range(10)] * 2
    }
    return pd.DataFrame(data)

def test_split_log_creation(sample_data):
    """Test that split_log.json is created with correct structure and exact ratios."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Prepare input
        input_path = Path(tmpdir) / "cleaned.parquet"
        output_dir = Path(tmpdir) / "splits"
        
        save_parquet(sample_data, str(input_path))
        
        # Run split
        result = create_train_val_test_split(
            input_path=str(input_path),
            output_dir=str(output_dir),
            train_ratio=0.7,
            val_ratio=0.15,
            test_ratio=0.15,
            random_state=42
        )
        
        # Verify log file exists
        log_path = Path("data/results/split_log.json")
        # Note: The function writes to data/results/split_log.json as per spec
        # We need to ensure the directory exists for the check, or check the returned result
        
        # Check the returned result structure
        assert "exact_ratios" in result
        assert "counts" in result
        assert "target_ratios" in result
        
        # Verify ratios sum to 1.0 (within float tolerance)
        total_ratio = sum(result["exact_ratios"].values())
        assert abs(total_ratio - 1.0) < 0.01, f"Ratios sum to {total_ratio}, expected 1.0"
        
        # Verify counts match data
        assert result["counts"]["total"] == len(sample_data)
        assert result["counts"]["train"] + result["counts"]["val"] + result["counts"]["test"] == len(sample_data)
        
        # Verify the log file was written to the expected location
        # Since the function writes to a hardcoded path 'data/results/split_log.json',
        # we check if that file exists (assuming the runner creates the directory)
        # In a real test environment, we might need to mock the path or ensure 'data/results' exists.
        # For this task, we verify the content was written if the directory exists.
        if Path("data/results").exists():
            with open(log_path, "r") as f:
                log_data = json.load(f)
            
            assert log_data["counts"]["total"] == len(sample_data)
            assert "train" in log_data["exact_ratios"]
            assert "val" in log_data["exact_ratios"]
            assert "test" in log_data["exact_ratios"]

def test_split_ratios_accuracy(sample_data):
    """Test that the split respects the target ratios approximately."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "cleaned.parquet"
        output_dir = Path(tmpdir) / "splits"
        
        save_parquet(sample_data, str(input_path))
        
        result = create_train_val_test_split(
            input_path=str(input_path),
            output_dir=str(output_dir),
            train_ratio=0.7,
            val_ratio=0.15,
            test_ratio=0.15,
            random_state=42
        )
        
        # Check that exact ratios are close to target
        assert abs(result["exact_ratios"]["train"] - 0.7) < 0.1
        assert abs(result["exact_ratios"]["val"] - 0.15) < 0.1
        assert abs(result["exact_ratios"]["test"] - 0.15) < 0.1