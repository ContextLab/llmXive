import pytest
import json
import torch
from pathlib import Path
from safetensors.torch import save_file
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_loader import (
    get_project_root,
    ensure_download_dir,
    compute_sha256_file,
    generate_procedural_source_loras,
    load_and_verify_source_loras,
    check_lora_compatibility,
    compute_source_ranks,
    merge_collection_lora,
    compute_merged_ranks,
    load_fp16_adapter_and_base_model
)

@pytest.fixture
def temp_project_root(tmp_path):
    """Creates a temporary project root structure."""
    # Create necessary directories
    dirs = [
        "data/models/source_loras",
        "data/models",
        "state",
        "data"
    ]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    
    # Mock the get_project_root function to return tmp_path
    import data_loader
    original_get_root = data_loader.get_project_root
    data_loader.get_project_root = lambda: tmp_path
    
    yield tmp_path
    
    # Restore original function
    data_loader.get_project_root = original_get_root

def test_generate_procedural_source_loras(temp_project_root):
    paths = generate_procedural_source_loras(num_effects=5)
    assert len(paths) == 5
    for effect, path in paths.items():
        assert path.exists()
        assert path.suffix == ".safetensors"

def test_check_lora_compatibility(temp_project_root):
    paths = generate_procedural_source_loras(num_effects=5)
    assert check_lora_compatibility(paths) is True

def test_compute_source_ranks(temp_project_root):
    paths = generate_procedural_source_loras(num_effects=5)
    ranks = compute_source_ranks(paths)
    assert len(ranks) == 5
    for rank in ranks.values():
        assert isinstance(rank, int)
        assert rank > 0

def test_merge_collection_lora(temp_project_root):
    source_paths = generate_procedural_source_loras(num_effects=5)
    output_path = temp_project_root / "data/models/collection_lora.safetensors"
    result_path = merge_collection_lora(source_paths, output_path)
    assert result_path.exists()

def test_compute_merged_ranks(temp_project_root):
    # Setup: Generate source, merge, then compute merged ranks
    source_paths = generate_procedural_source_loras(num_effects=5)
    output_path = temp_project_root / "data/models/collection_lora.safetensors"
    merge_collection_lora(source_paths, output_path)
    
    ranks = compute_merged_ranks()
    assert len(ranks) == 5
    assert "subspace_ranks_merged.json" in str(temp_project_root / "data/subspace_ranks_merged.json")
    assert (temp_project_root / "data/subspace_ranks_merged.json").exists()

def test_load_fp16_adapter_and_base_model_defaults(temp_project_root):
    # Setup: Create the expected adapter file
    adapter_path = temp_project_root / "data/models/collection_lora.safetensors"
    save_file({"dummy": torch.tensor([1.0])}, str(adapter_path))
    
    adapter, base = load_fp16_adapter_and_base_model()
    assert adapter == adapter_path
    assert base == temp_project_root / "data/models/base/placeholder.safetensors"

def test_load_fp16_adapter_and_base_model_args(temp_project_root):
    adapter_path = temp_project_root / "data/models/collection_lora.safetensors"
    save_file({"dummy": torch.tensor([1.0])}, str(adapter_path))
    
    # Test positional args
    adapter, base = load_fp16_adapter_and_base_model(str(adapter_path), "custom_base.safetensors")
    assert adapter == adapter_path
    assert base == Path("custom_base.safetensors")
    
    # Test keyword args
    adapter, base = load_fp16_adapter_and_base_model(adapter_path=str(adapter_path), base_model_path="another_base.safetensors")
    assert adapter == adapter_path
    assert base == Path("another_base.safetensors")

def test_load_fp16_adapter_not_found(temp_project_root):
    with pytest.raises(FileNotFoundError):
        load_fp16_adapter_and_base_model()