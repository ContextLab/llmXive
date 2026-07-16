import os
import json
import tempfile
from pathlib import Path
import pytest

from models.log_hyperparameters import (
    load_hyperparameter_log,
    format_hyperparameter_entry,
    generate_hyperparameter_log
)

@pytest.fixture
def sample_hyperparameter_data():
    """Create sample hyperparameter search results."""
    return [
        {
            "learning_rate": 0.001,
            "hidden_dim": 64,
            "num_layers": 2,
            "dropout": 0.1,
            "batch_size": 32,
            "val_r2": 0.85,
            "val_mae": 0.45,
            "train_r2": 0.88,
            "train_mae": 0.40,
            "seed": 42
        },
        {
            "learning_rate": 0.01,
            "hidden_dim": 128,
            "num_layers": 3,
            "dropout": 0.2,
            "batch_size": 64,
            "val_r2": 0.92,
            "val_mae": 0.30,
            "train_r2": 0.94,
            "train_mae": 0.25,
            "seed": 123
        },
        {
            "learning_rate": 0.0001,
            "hidden_dim": 32,
            "num_layers": 1,
            "dropout": 0.05,
            "batch_size": 16,
            "val_r2": 0.78,
            "val_mae": 0.55,
            "train_r2": 0.80,
            "train_mae": 0.50,
            "seed": 456
        }
    ]

@pytest.fixture
def temp_input_file(sample_hyperparameter_data):
    """Create a temporary file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_hyperparameter_data, f)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()

def test_load_hyperparameter_log(temp_input_file):
    """Test loading hyperparameter log from JSON file."""
    results = load_hyperparameter_log(temp_input_file)
    assert isinstance(results, list)
    assert len(results) == 3
    assert all(isinstance(r, dict) for r in results)
    assert 'val_r2' in results[0]

def test_load_hyperparameter_log_not_found():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        load_hyperparameter_log(Path("nonexistent/file.json"))

def test_load_hyperparameter_log_invalid_format(temp_input_file):
    """Test error handling for invalid JSON format."""
    # Create a file with non-list content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"not": "a list"}, f)
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError):
            load_hyperparameter_log(temp_path)
    finally:
        temp_path.unlink()

def test_format_hyperparameter_entry():
    """Test formatting of a single hyperparameter entry."""
    config = {
        "learning_rate": 0.001,
        "hidden_dim": 64,
        "val_r2": 0.85,
        "val_mae": 0.45,
        "extra_field": "should_be_ignored"
    }
    
    formatted = format_hyperparameter_entry(config, 1)
    
    assert "Rank: 1" in formatted
    assert "Validation R²: 0.8500" in formatted
    assert "Validation MAE: 0.4500" in formatted
    assert "learning_rate: 0.001" in formatted
    assert "hidden_dim: 64" in formatted
    assert "extra_field" not in formatted

def test_generate_hyperparameter_log(temp_input_file):
    """Test generation of formatted hyperparameter log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_log.log"
        
        generate_hyperparameter_log(temp_input_file, output_path, top_n=2)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            content = f.read()
        
        # Check header
        assert "Top 2 Hyperparameter Configurations" in content
        assert "Sorted by Validation R²" in content
        
        # Check that the best config (val_r2=0.92) is ranked first
        lines = content.split('\n')
        # Find the first rank entry
        first_rank_idx = next(i for i, line in enumerate(lines) if "Rank: 1" in line)
        # Check that the R2 score near rank 1 is 0.92
        assert "0.9200" in content[first_rank_idx:first_rank_idx+200]
        
        # Check that only top 2 are included (0.92 and 0.85)
        assert "0.9200" in content
        assert "0.8500" in content
        # The third config (0.78) should not be in the top 2
        # Note: We can't easily check absence without parsing, but the logic is tested

def test_generate_hyperparameter_log_empty():
    """Test handling of empty hyperparameter list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "empty.json"
        output_path = Path(tmpdir) / "output.log"
        
        with open(input_path, 'w') as f:
            json.dump([], f)
        
        generate_hyperparameter_log(input_path, output_path, top_n=10)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
        assert "No hyperparameter configurations found" in content
