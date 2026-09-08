import pytest
import json
import os
from pathlib import Path
import tempfile
import numpy as np

# Import the class to test
from code.ingest import RealDataLoader, DataAvailabilityError
from code.config import Config, RunMode
from code.models import AtomicSnapshot

class MockConfig:
    def __init__(self, raw_dir: Path, processed_dir: Path):
        self._raw = raw_dir
        self._processed = processed_dir
    
    def get_raw_data_path(self) -> Path:
        return self._raw
    
    def get_processed_data_path(self) -> Path:
        return self._processed

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw"
        processed = Path(tmp) / "processed"
        raw.mkdir()
        processed.mkdir()
        yield raw, processed

def create_valid_xyz_file(path: Path, has_tc: bool = True):
    """Creates a minimal .xyz file with valid metadata."""
    content = f"""3
    Test snapshot
    thermal_conductivity_W_m_K=5.5
    """
    # Add atoms
    for i, elem in enumerate(['Cu', 'Ni', 'Cu']):
        content += f"{elem} {i*2.0} {i*2.0} {i*2.0}\n"
    
    if not has_tc:
        # Remove the TC line if requested
        lines = content.split('\n')
        lines = [l for l in lines if 'thermal_conductivity' not in l]
        content = '\n'.join(lines)

    with open(path, 'w') as f:
        f.write(content)

def test_real_data_loader_missing_thermal_conductivity(temp_data_dir):
    """
    T013 Requirement: Raise DataAvailabilityError with specific message 
    "Missing thermal conductivity" if the key is missing.
    """
    raw_dir, processed_dir = temp_data_dir
    create_valid_xyz_file(raw_dir / "no_tc.xyz", has_tc=False)
    
    config = MockConfig(raw_dir, processed_dir)
    loader = RealDataLoader(config)
    
    with pytest.raises(DataAvailabilityError) as excinfo:
        loader.load_from_directory(raw_dir)
    
    assert "Missing thermal conductivity" in str(excinfo.value)

def test_real_data_loader_success(temp_data_dir):
    """
    T013 Requirement: Parse snapshots and save to parquet if valid.
    """
    raw_dir, processed_dir = temp_data_dir
    create_valid_xyz_file(raw_dir / "good.xyz", has_tc=True)
    
    config = MockConfig(raw_dir, processed_dir)
    loader = RealDataLoader(config)
    
    # Should not raise
    snapshots = loader.load_from_directory(raw_dir)
    
    assert len(snapshots) == 1
    assert snapshots[0].thermal_conductivity_W_m_K == 5.5
    
    # Check parquet file creation (via save_to_parquet called internally in pipeline, 
    # but here we test the loader's save method directly or via a modified flow)
    # Since load_from_directory doesn't save, we call save explicitly for this test
    output_path = processed_dir / "raw_snapshots.parquet"
    loader.save_to_parquet(snapshots, output_path)
    
    assert output_path.exists()
    
    # Verify content
    import pandas as pd
    df = pd.read_parquet(output_path)
    assert len(df) == 1
    assert df.iloc[0]['thermal_conductivity_W_m_K'] == 5.5

def test_real_data_loader_no_files(temp_data_dir):
    """
    T013 Requirement: Raise FileNotFoundError if no data found.
    """
    raw_dir, processed_dir = temp_data_dir
    
    config = MockConfig(raw_dir, processed_dir)
    loader = RealDataLoader(config)
    
    with pytest.raises(FileNotFoundError):
        loader.load_from_directory(raw_dir)