import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.simulation.logger import setup_logger, inject_batch_context, save_seed_config
from code.simulation.schema import validate_seed_config


def test_inject_batch_context_includes_batch_id():
    """Test that inject_batch_context sets batch_id and seed in the logger."""
    logger = setup_logger("test_batch")
    inject_batch_context(logger, batch_id="batch_123", seed=42)
    
    # Log an entry to see if context is included
    entry = logger.log("test_operation", param="value")
    
    assert entry.batch_id == "batch_123"
    assert entry.seed == 42
    assert entry.operation == "test_operation"


def test_inject_batch_context_persists_across_logs():
    """Test that batch context persists for all subsequent logs."""
    logger = setup_logger("persistent_test")
    inject_batch_context(logger, batch_id="batch_456", seed=99)
    
    entry1 = logger.log("op1")
    entry2 = logger.log("op2")
    
    assert entry1.batch_id == "batch_456"
    assert entry1.seed == 99
    assert entry2.batch_id == "batch_456"
    assert entry2.seed == 99


def test_save_seed_config_creates_file_and_populates():
    """Test that save_seed_config creates the file and populates it correctly."""
    temp_dir = Path("data/config")
    temp_dir.mkdir(parents=True, exist_ok=True)
    config_file = temp_dir / "seed_config.json"
    
    # Clean up if exists
    if config_file.exists():
        config_file.unlink()
    
    batch_id = "test_batch_001"
    seed = 12345
    config_hash = "abc123def456"
    
    result = save_seed_config(batch_id, seed, config_hash)
    
    # Verify file exists
    assert config_file.exists()
    
    # Verify content
    with open(config_file, 'r') as f:
        saved_config = json.load(f)
    
    assert batch_id in saved_config
    assert saved_config[batch_id]["seed"] == seed
    assert saved_config[batch_id]["timestamp"] is not None
    assert saved_config[batch_id]["config_hash"] == config_hash
    
    # Verify structure matches schema
    validate_seed_config(saved_config)


def test_save_seed_config_appends_without_overwriting():
    """Test that save_seed_config appends new entries without overwriting existing ones."""
    temp_dir = Path("data/config")
    temp_dir.mkdir(parents=True, exist_ok=True)
    config_file = temp_dir / "seed_config.json"
    
    # Initialize with one entry
    existing_data = {
        "batch_001": {"seed": 100, "timestamp": "2023-01-01T00:00:00", "config_hash": "hash1"}
    }
    with open(config_file, 'w') as f:
        json.dump(existing_data, f)
    
    # Add a new entry
    new_batch_id = "batch_002"
    new_seed = 200
    new_hash = "hash2"
    
    result = save_seed_config(new_batch_id, new_seed, new_hash)
    
    # Verify both entries exist
    assert "batch_001" in result
    assert "batch_002" in result
    assert result["batch_001"]["seed"] == 100
    assert result["batch_002"]["seed"] == 200


def test_save_seed_config_raises_on_duplicate_batch_id():
    """Test that save_seed_config raises RuntimeError if batch_id already exists."""
    temp_dir = Path("data/config")
    temp_dir.mkdir(parents=True, exist_ok=True)
    config_file = temp_dir / "seed_config.json"
    
    # Initialize with one entry
    existing_data = {
        "batch_duplicate": {"seed": 100, "timestamp": "2023-01-01T00:00:00", "config_hash": "hash1"}
    }
    with open(config_file, 'w') as f:
        json.dump(existing_data, f)
    
    # Try to add the same batch_id again
    with pytest.raises(RuntimeError, match="already exists"):
        save_seed_config("batch_duplicate", 200, "hash2")
