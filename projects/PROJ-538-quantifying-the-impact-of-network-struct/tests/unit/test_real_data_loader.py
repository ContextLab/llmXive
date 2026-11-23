import pytest
import os
import json
import tempfile
from pathlib import Path
import numpy as np
from ase import Atoms
from ase.io import write
import pyarrow.parquet as pq

from code.config import Config, RunMode
from code.ingest import RealDataLoader, DataAvailabilityError
from code.models import AtomicSnapshot

@pytest.fixture
def temp_config():
    """Creates a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        raw_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        
        # Create a minimal config
        config = Config(
            run_mode=RunMode.REAL,
            data_dir=data_dir,
            raw_dir=raw_dir,
            processed_dir=processed_dir
        )
        yield config

def test_load_snapshot_with_thermal_conductivity(temp_config):
    """Test that a snapshot with thermal conductivity is loaded correctly."""
    # Create a dummy XYZ file with metadata
    atoms = Atoms('Cu4Ni4', 
                  positions=np.random.rand(8, 3) * 5,
                  cell=[5, 5, 5],
                  pbc=True)
    
    # Add thermal conductivity to info
    atoms.info['thermal_conductivity_W_m_K'] = 100.0
    
    xyz_file = temp_config.raw_data_dir / "test_snapshot.xyz"
    write(xyz_file, atoms)
    
    # Create a sidecar JSON (optional, but good for testing sidecar logic)
    # We rely on atoms.info here.
    
    loader = RealDataLoader(temp_config)
    snapshots = loader.load_snapshots()
    
    assert len(snapshots) == 1
    assert snapshots[0].thermal_conductivity_W_m_K == 100.0
    assert snapshots[0].species == ['Cu', 'Cu', 'Cu', 'Cu', 'Ni', 'Ni', 'Ni', 'Ni']

def test_load_snapshot_missing_thermal_conductivity_raises(temp_config):
    """Test that a snapshot without thermal conductivity raises DataAvailabilityError."""
    # Create a dummy XYZ file WITHOUT thermal conductivity
    atoms = Atoms('Cu4Ni4', 
                  positions=np.random.rand(8, 3) * 5,
                  cell=[5, 5, 5],
                  pbc=True)
    # Ensure key is NOT in info
    if 'thermal_conductivity_W_m_K' in atoms.info:
        del atoms.info['thermal_conductivity_W_m_K']
    
    xyz_file = temp_config.raw_data_dir / "test_missing.xyz"
    write(xyz_file, atoms)
    
    loader = RealDataLoader(temp_config)
    
    with pytest.raises(DataAvailabilityError) as exc_info:
        loader.load_snapshots()
    
    assert "Missing thermal conductivity" in str(exc_info.value)

def test_save_to_parquet(temp_config):
    """Test that snapshots are saved to Parquet correctly."""
    # Create a valid snapshot
    atoms = Atoms('Cu2Ni2', 
                  positions=np.random.rand(4, 3) * 5,
                  cell=[5, 5, 5],
                  pbc=True)
    atoms.info['thermal_conductivity_W_m_K'] = 50.0
    
    xyz_file = temp_config.raw_data_dir / "test_save.xyz"
    write(xyz_file, atoms)
    
    loader = RealDataLoader(temp_config)
    snapshots = loader.load_snapshots()
    output_path = loader.save_to_parquet(snapshots)
    
    assert output_path.exists()
    
    # Verify contents
    table = pq.read_table(output_path)
    df = table.to_pandas()
    
    assert len(df) == 1
    assert df['thermal_conductivity_W_m_K'].iloc[0] == 50.0
    assert df['source_file'].iloc[0].endswith('test_save.xyz')