import os
import tempfile
import shutil
from pathlib import Path
import torch
import numpy as np
import pytest

from src.analysis.accumulate_opd import (
    find_layer_files,
    load_and_flatten_layer,
    aggregate_opd_updates
)

@pytest.fixture
def temp_run_dir():
    """Create a temporary directory structure mimicking OPD outputs."""
    tmpdir = tempfile.mkdtemp()
    base = Path(tmpdir)
    
    # Create structure: results/opd/updates_seed_0/step_0/layer_XX.pt
    step_dir = base / "opd" / "updates_seed_0" / "step_0"
    step_dir.mkdir(parents=True)
    
    # Create dummy layer files
    # Layer 0: shape (10,)
    torch.save(torch.arange(10, dtype=torch.float32), step_dir / "layer_00.pt")
    # Layer 1: shape (5,)
    torch.save(torch.arange(5, dtype=torch.float32), step_dir / "layer_01.pt")
    
    # Create another step
    step_dir2 = base / "opd" / "updates_seed_0" / "step_1"
    step_dir2.mkdir()
    torch.save(torch.arange(10, dtype=torch.float32) * 2, step_dir2 / "layer_00.pt")
    torch.save(torch.arange(5, dtype=torch.float32) * 2, step_dir2 / "layer_01.pt")
    
    yield base
    
    shutil.rmtree(tmpdir)

def test_find_layer_files(temp_run_dir):
    step_path = temp_run_dir / "opd" / "updates_seed_0" / "step_0"
    files = find_layer_files(step_path)
    assert len(files) == 2
    # Check sorting
    assert files[0].name == "layer_00.pt"
    assert files[1].name == "layer_01.pt"

def test_load_and_flatten_layer(temp_run_dir):
    file_path = temp_run_dir / "opd" / "updates_seed_0" / "step_0" / "layer_00.pt"
    tensor = load_and_flatten_layer(file_path)
    assert tensor.shape == (10,)
    assert torch.allclose(tensor, torch.arange(10, dtype=torch.float32))

def test_aggregate_opd_updates(temp_run_dir):
    seed = 0
    base_dir = temp_run_dir / "opd"
    
    # Ensure output directory exists for the function to write to
    # The function expects base_output_dir to contain 'opd'
    # But our temp_run_dir is the base.
    # Let's adjust: aggregate_opd_updates expects base_output_dir / "opd" / ...
    # So we pass temp_run_dir as base_output_dir.
    
    result = aggregate_opd_updates(
        seed=seed,
        base_output_dir=temp_run_dir,
        output_filename="test_accumulated.npy"
    )
    
    # Expected shape: (steps=2, n_params=10+5=15)
    assert result.shape == (2, 15)
    
    # Check values
    # Step 0: [0..9, 0..4]
    expected_step0 = torch.cat([torch.arange(10), torch.arange(5)]).numpy()
    # Step 1: [0..9]*2, [0..4]*2
    expected_step1 = torch.cat([torch.arange(10)*2, torch.arange(5)*2]).numpy()
    
    np.testing.assert_array_equal(result[0], expected_step0)
    np.testing.assert_array_equal(result[1], expected_step1)
    
    # Verify file was saved
    saved_file = temp_run_dir / "opd" / "test_accumulated.npy"
    assert saved_file.exists()

def test_aggregate_no_files_raises():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "opd" / "updates_seed_99").mkdir(parents=True)
        
        with pytest.raises(FileNotFoundError):
            aggregate_opd_updates(seed=99, base_output_dir=base)

def test_aggregate_missing_dir_raises():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        # Directory does not exist
        with pytest.raises(FileNotFoundError):
            aggregate_opd_updates(seed=99, base_output_dir=base)