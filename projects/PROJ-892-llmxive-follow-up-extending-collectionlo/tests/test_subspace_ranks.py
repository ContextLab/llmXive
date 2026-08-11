import pytest
import torch
import json
import os
from pathlib import Path
from code.data_loader import compute_subspace_ranks, save_adapter_weights

def test_compute_subspace_ranks_creates_file():
    """Test that compute_subspace_ranks creates the output JSON file."""
    # Create a temporary mock adapter
    mock_dir = Path("data/models")
    mock_dir.mkdir(parents=True, exist_ok=True)
    
    mock_adapter_path = mock_dir / "test_adapter.safetensors"
    mock_output_path = Path("data/test_subspace_ranks.json")
    
    # Create a simple LoRA-like structure
    # lora_down: (rank, in_features) -> e.g., (4, 10)
    # lora_up: (out_features, rank) -> e.g., (20, 4)
    weights = {
        "layer1.lora_down.weight": torch.randn(4, 10),
        "layer1.lora_up.weight": torch.randn(20, 4),
        "layer2.lora_down.weight": torch.randn(8, 5),
        "layer2.lora_up.weight": torch.randn(15, 8),
    }
    
    save_adapter_weights(weights, mock_adapter_path)
    
    # Run the function
    ranks = compute_subspace_ranks(mock_adapter_path, mock_output_path)
    
    # Assertions
    assert mock_output_path.exists(), "Output JSON file was not created."
    assert isinstance(ranks, dict), "Return value should be a dictionary."
    assert "layer1" in ranks or "layer1.lora_down" in ranks or "layer1" in str(list(ranks.keys())[0]), "Expected layer keys in result."
    
    # Check specific ranks (random tensors should have full rank for small sizes)
    # With tolerance 1e-4, random float tensors usually have full rank
    assert all(isinstance(v, int) for v in ranks.values()), "All ranks should be integers."
    
    # Cleanup
    if mock_adapter_path.exists():
        mock_adapter_path.unlink()
    if mock_output_path.exists():
        mock_output_path.unlink()

def test_compute_subspace_ranks_tolerance():
    """Test that tolerance threshold correctly reduces rank."""
    mock_dir = Path("data/models")
    mock_dir.mkdir(parents=True, exist_ok=True)
    
    mock_adapter_path = mock_dir / "test_tolerance_adapter.safetensors"
    mock_output_path = Path("data/test_tolerance_ranks.json")
    
    # Create a matrix with known rank: 2 non-zero singular values, rest tiny
    # Shape (10, 10), rank 2
    matrix = torch.zeros(10, 10)
    matrix[0, 0] = 10.0
    matrix[1, 1] = 5.0
    # Add noise smaller than tolerance
    matrix[2, 2] = 1e-6 
    
    weights = {
        "test_layer.lora_down.weight": matrix,
        "test_layer.lora_up.weight": torch.randn(10, 10),
    }
    
    save_adapter_weights(weights, mock_adapter_path)
    
    ranks = compute_subspace_ranks(mock_adapter_path, mock_output_path, tolerance=1e-4)
    
    # The effective rank should be 2 (10.0 and 5.0 are > 1e-4, 1e-6 is not)
    # Depending on key parsing, the key might be "test_layer" or similar
    found_rank = False
    for k, v in ranks.items():
        if v == 2:
            found_rank = True
            break
    
    assert found_rank, f"Expected rank 2 for test_layer, got ranks: {ranks}"
    
    # Cleanup
    if mock_adapter_path.exists():
        mock_adapter_path.unlink()
    if mock_output_path.exists():
        mock_output_path.unlink()