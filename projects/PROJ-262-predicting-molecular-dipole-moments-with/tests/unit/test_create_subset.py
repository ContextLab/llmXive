import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.create_subset import create_reproducible_subset

def test_create_reproducible_subset_fixed_size():
    """Test that the subset function creates a file with exactly the requested size."""
    # Create a mock .npz file with dummy data
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        npz_path = tmpdir_path / "test_data.npz"
        
        # Create dummy data: 10000 molecules
        n_total = 10000
        dummy_data = {
            'atom_numbers': np.random.randint(1, 10, size=(n_total, 9)),
            'dipole': np.random.rand(n_total, 3)
        }
        np.savez(npz_path, **dummy_data)
        
        output_path = tmpdir_path / "subset.parquet"
        target_size = 5000
        seed = 42
        
        # Run the function
        create_reproducible_subset(tmpdir_path, output_path, target_size, seed)
        
        # Verify output exists
        assert output_path.exists(), "Output Parquet file was not created."
        
        # Load and verify size
        df = pd.read_parquet(output_path)
        assert len(df) == target_size, f"Expected {target_size} rows, got {len(df)}"
        
        # Verify columns
        assert 'molecule_id' in df.columns
        assert 'original_index' in df.columns
        assert 'dipole_magnitude' in df.columns

def test_create_reproducible_subset_deterministic():
    """Test that running with the same seed produces the same subset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        npz_path = tmpdir_path / "test_data.npz"
        
        # Create dummy data
        n_total = 1000
        dummy_data = {
            'atom_numbers': np.random.randint(1, 10, size=(n_total, 9)),
            'dipole': np.random.rand(n_total, 3)
        }
        np.savez(npz_path, **dummy_data)
        
        output_path1 = tmpdir_path / "subset1.parquet"
        output_path2 = tmpdir_path / "subset2.parquet"
        size = 100
        seed = 42
        
        # Run twice
        create_reproducible_subset(tmpdir_path, output_path1, size, seed)
        create_reproducible_subset(tmpdir_path, output_path2, size, seed)
        
        # Load and compare
        df1 = pd.read_parquet(output_path1)
        df2 = pd.read_parquet(output_path2)
        
        assert df1.equals(df2), "Subset is not deterministic with the same seed."

def test_create_reproducible_subset_parquet_format():
    """Test that the output is a valid Parquet file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        npz_path = tmpdir_path / "test_data.npz"
        
        n_total = 1000
        dummy_data = {
            'atom_numbers': np.random.randint(1, 10, size=(n_total, 9)),
            'dipole': np.random.rand(n_total, 3)
        }
        np.savez(npz_path, **dummy_data)
        
        output_path = tmpdir_path / "subset.parquet"
        create_reproducible_subset(tmpdir_path, output_path, 100, 42)
        
        # Try to read it back as parquet
        try:
            df = pd.read_parquet(output_path)
            assert isinstance(df, pd.DataFrame)
        except Exception as e:
            pytest.fail(f"Failed to read output as Parquet: {e}")