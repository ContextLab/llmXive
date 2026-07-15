import os
import json
import tempfile
import torch
import pytest
from pathlib import Path

from checkpoint_manager import (
    save_checkpoint,
    load_checkpoint,
    compute_file_checksum,
    validate_checkpoint_metadata,
    list_checkpoints
)
from vae_model import VAE

@pytest.fixture
def temp_checkpoint_dir():
    """Create a temporary directory for checkpoint tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def dummy_model():
    """Create a dummy VAE model for testing."""
    return VAE(input_dim=3, latent_dim=10, hidden_dims=[64, 32])

@pytest.fixture
def dummy_optimizer(dummy_model):
    """Create a dummy optimizer for testing."""
    return torch.optim.Adam(dummy_model.parameters(), lr=1e-3)

def test_compute_file_checksum(temp_checkpoint_dir):
    """Test checksum computation on a known file."""
    test_file = Path(temp_checkpoint_dir) / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = compute_file_checksum(test_file)
    assert len(checksum) == 64  # SHA-256 hex length
    assert isinstance(checksum, str)

def test_validate_checkpoint_metadata_valid():
    """Test validation with valid metadata."""
    metadata = {
        "epoch": 10,
        "loss": 0.5,
        "timestamp": "2023-01-01T00:00:00",
        "model_checksum": "abc123",
        "dataset_checksum": "def456"
    }
    assert validate_checkpoint_metadata(metadata) is True

def test_validate_checkpoint_metadata_missing_field():
    """Test validation fails with missing required field."""
    metadata = {
        "epoch": 10,
        "loss": 0.5,
        "timestamp": "2023-01-01T00:00:00"
        # Missing model_checksum and dataset_checksum
    }
    with pytest.raises(ValueError, match="Missing required metadata field"):
        validate_checkpoint_metadata(metadata)

def test_validate_checkpoint_metadata_invalid_types():
    """Test validation fails with invalid types."""
    metadata = {
        "epoch": "ten",  # Should be int
        "loss": 0.5,
        "timestamp": "2023-01-01T00:00:00",
        "model_checksum": "abc123",
        "dataset_checksum": "def456"
    }
    with pytest.raises(ValueError, match="Epoch must be an integer"):
        validate_checkpoint_metadata(metadata)

def test_save_and_load_checkpoint(dummy_model, dummy_optimizer, temp_checkpoint_dir):
    """Test saving and loading a checkpoint."""
    model_path, checksum = save_checkpoint(
        model=dummy_model,
        epoch=5,
        loss=0.123,
        optimizer=dummy_optimizer,
        metadata={"dataset_checksum": "test_ds_123"},
        checkpoint_dir=temp_checkpoint_dir
    )
    
    assert model_path.exists()
    assert checksum is not None
    assert len(checksum) == 64
    
    # Load the checkpoint
    loaded_epoch, loaded_loss, loaded_model, loaded_optimizer, metadata = load_checkpoint(
        checkpoint_path=model_path,
        model=VAE(input_dim=3, latent_dim=10, hidden_dims=[64, 32]),
        optimizer=dummy_optimizer
    )
    
    assert loaded_epoch == 5
    assert abs(loaded_loss - 0.123) < 1e-6
    assert metadata["epoch"] == 5
    assert metadata["model_checksum"] == checksum

def test_save_and_load_checkpoint_checksum_mismatch(dummy_model, dummy_optimizer, temp_checkpoint_dir):
    """Test that loading a modified checkpoint raises an error."""
    model_path, _ = save_checkpoint(
        model=dummy_model,
        epoch=5,
        loss=0.123,
        optimizer=dummy_optimizer,
        checkpoint_dir=temp_checkpoint_dir
    )
    
    # Corrupt the checkpoint file
    with open(model_path, "ab") as f:
        f.write(b"corruption")
    
    with pytest.raises(ValueError, match="Checkpoint checksum mismatch"):
        load_checkpoint(
            checkpoint_path=model_path,
            model=VAE(input_dim=3, latent_dim=10, hidden_dims=[64, 32]),
            optimizer=dummy_optimizer,
            strict=True
        )

def test_list_checkpoints(temp_checkpoint_dir, dummy_model, dummy_optimizer):
    """Test listing checkpoints."""
    # Save multiple checkpoints
    for i in [1, 5, 10]:
        save_checkpoint(
            model=dummy_model,
            epoch=i,
            loss=0.1,
            optimizer=dummy_optimizer,
            checkpoint_dir=temp_checkpoint_dir
        )
    
    checkpoints = list_checkpoints(temp_checkpoint_dir)
    assert len(checkpoints) == 3
    
    # Check sorting (descending by epoch)
    assert checkpoints[0]["epoch"] == 10
    assert checkpoints[1]["epoch"] == 5
    assert checkpoints[2]["epoch"] == 1
    
    # Check validity
    for ckpt in checkpoints:
        assert ckpt["valid"] is True

def test_list_checkpoints_empty_directory(temp_checkpoint_dir):
    """Test listing checkpoints in empty directory."""
    checkpoints = list_checkpoints(temp_checkpoint_dir)
    assert len(checkpoints) == 0

def test_load_checkpoint_nonexistent_file(dummy_model, dummy_optimizer):
    """Test loading a non-existent checkpoint."""
    fake_path = Path("/nonexistent/path/checkpoint.pt")
    with pytest.raises(FileNotFoundError):
        load_checkpoint(
            checkpoint_path=fake_path,
            model=dummy_model,
            optimizer=dummy_optimizer
        )
