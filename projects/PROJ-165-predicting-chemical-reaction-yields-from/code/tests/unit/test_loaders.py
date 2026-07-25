import pytest
import torch
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.loaders import ReactionSample, create_dataloader

@pytest.fixture
def temp_dataset():
    """Create a temporary dataset file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "test_data.parquet"
        
        # Create dummy data
        n_samples = 10
        n_fp = 1024
        n_cond = 5
        n_spec_len = 100
        
        data = {}
        
        # Target
        data['normalized_dft_energy'] = np.random.rand(n_samples) * 10 - 5
        
        # Fingerprints
        for i in range(n_fp):
            data[f'fp_{i}'] = np.random.randint(0, 2, n_samples)
        
        # Conditions
        for i in range(n_cond):
            data[f'cond_{i}'] = np.random.randint(0, 2, n_samples)
        
        # Spectra (fixed length)
        for i in range(n_spec_len):
            data[f'ir_{i}'] = np.random.rand(n_samples)
            data[f'raman_{i}'] = np.random.rand(n_samples)
            data[f'nmr_{i}'] = np.random.rand(n_samples)
        
        df = pd.DataFrame(data)
        df.to_parquet(data_path)
        
        yield data_path

def test_reaction_sample_init(temp_dataset):
    """Test initialization of ReactionSample dataset."""
    dataset = ReactionSample(data_path=temp_dataset)
    assert len(dataset) == 10
    assert dataset.target_column == "normalized_dft_energy"

def test_reaction_sample_getitem(temp_dataset):
    """Test retrieval of a single sample."""
    dataset = ReactionSample(data_path=temp_dataset)
    sample = dataset[0]
    
    assert 'spectra' in sample
    assert 'fingerprints' in sample
    assert 'conditions' in sample
    assert 'target' in sample
    assert 'mask' in sample
    
    # Check shapes
    assert sample['spectra'].shape == (3, 100) # 3 channels, 100 length
    assert sample['fingerprints'].shape == (1024,)
    assert sample['conditions'].shape == (5,)
    assert sample['target'].shape == ()
    assert sample['mask'].shape == (3,)
    
    # Check types
    assert isinstance(sample['spectra'], torch.Tensor)
    assert isinstance(sample['target'], torch.Tensor)

def test_missing_channels_masking(temp_dataset):
    """Test that missing channels are properly masked."""
    dataset = ReactionSample(
        data_path=temp_dataset,
        missing_channels=['ir', 'raman']
    )
    sample = dataset[0]
    
    # Mask should indicate IR and Raman are invalid (0.0)
    assert sample['mask'][0] == 0.0 # IR
    assert sample['mask'][1] == 0.0 # Raman
    assert sample['mask'][2] == 1.0 # NMR
    
    # Values in masked channels should be the mask value (default 0.0)
    assert torch.allclose(sample['spectra'][0], torch.zeros_like(sample['spectra'][0]))
    assert torch.allclose(sample['spectra'][1], torch.zeros_like(sample['spectra'][1]))
    # NMR should have non-zero values (unless random chance, but unlikely to be all zero)
    # We just check it's not explicitly forced to mask value by our logic if data existed
    # (Here we assume data exists)

def test_create_dataloader(temp_dataset):
    """Test creation of DataLoader."""
    loader = create_dataloader(
        data_path=temp_dataset,
        batch_size=4,
        shuffle=False
    )
    
    assert loader is not None
    
    # Iterate once
    batch = next(iter(loader))
    
    assert 'spectra' in batch
    assert batch['spectra'].shape == (4, 3, 100)
    assert batch['fingerprints'].shape == (4, 1024)
    assert batch['conditions'].shape == (4, 5)
    assert batch['target'].shape == (4,)
    assert len(batch['index']) == 4

def test_nonexistent_file():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        ReactionSample(data_path="nonexistent.parquet")

def test_missing_target_column(temp_dataset):
    """Test that ValueError is raised if target column is missing."""
    # Rename the target column
    df = pd.read_parquet(temp_dataset)
    df.rename(columns={'normalized_dft_energy': 'wrong_target'}, inplace=True)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        new_path = Path(tmpdir) / "bad_target.parquet"
        df.to_parquet(new_path)
        
        with pytest.raises(ValueError):
            ReactionSample(data_path=new_path, target_column="normalized_dft_energy")
