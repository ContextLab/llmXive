import os
import json
import pandas as pd
import pytest
from pathlib import Path
import shutil
import tempfile

# Add code to path for imports
sys_path = str(Path(__file__).parent.parent.parent / "code")
if sys_path not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_path)

from test_split import load_data, create_test_set, save_test_set, save_indices, save_metadata

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

@pytest.fixture
def sample_raw_pool(temp_dir):
    """Create a sample raw_pool.csv file."""
    raw_pool_path = Path(temp_dir) / "data" / "raw"
    raw_pool_path.mkdir(parents=True, exist_ok=True)
    
    data = {
        'material_id': [f'mat_{i}' for i in range(100)],
        'composition': [f'Fe_{i}' for i in range(100)],
        'formation_energy': [i * 0.1 for i in range(100)],
        'dft_computed': [True] * 100
    }
    df = pd.DataFrame(data)
    file_path = raw_pool_path / "raw_pool.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)

@pytest.fixture
def sample_config(temp_dir):
    """Create a sample test_config.json file."""
    config_path = Path(temp_dir) / "data" / "metadata"
    config_path.mkdir(parents=True, exist_ok=True)
    
    config = {"test_size": 10}
    file_path = config_path / "test_config.json"
    with open(file_path, 'w') as f:
        json.dump(config, f)
    return str(file_path)

def test_load_data_success(sample_raw_pool):
    """Test successful loading of raw pool."""
    df = load_data(sample_raw_pool)
    assert len(df) == 100
    assert 'formation_energy' in df.columns

def test_load_data_missing_file(temp_dir):
    """Test RuntimeError when file is missing."""
    missing_path = str(Path(temp_dir) / "missing.csv")
    with pytest.raises(RuntimeError, match="missing"):
        load_data(missing_path)

def test_load_data_empty_file(temp_dir):
    """Test RuntimeError when file is empty."""
    empty_path = Path(temp_dir) / "empty.csv"
    empty_path.write_text("material_id,composition,formation_energy,dft_computed\n")
    with pytest.raises(RuntimeError, match="empty"):
        load_data(str(empty_path))

def test_create_test_set_stratification(sample_raw_pool, sample_config):
    """Test that test set is created with correct size and stratification."""
    df = load_data(sample_raw_pool)
    test_df, indices = create_test_set(df, sample_config)
    
    assert len(test_df) == 10  # As defined in config
    assert len(indices) == 10
    assert 'strata' in test_df.columns  # Temp column used for sampling

def test_save_test_set(temp_dir, sample_raw_pool, sample_config):
    """Test saving test set to CSV."""
    df = load_data(sample_raw_pool)
    test_df, _ = create_test_set(df, sample_config)
    
    output_path = Path(temp_dir) / "test_set.csv"
    save_test_set(test_df, str(output_path))
    
    assert output_path.exists()
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == 10

def test_save_indices(temp_dir, sample_raw_pool, sample_config):
    """Test saving indices to CSV."""
    df = load_data(sample_raw_pool)
    _, indices = create_test_set(df, sample_config)
    
    output_path = Path(temp_dir) / "indices.csv"
    save_indices(indices, str(output_path))
    
    assert output_path.exists()
    saved_df = pd.read_csv(output_path)
    assert len(saved_df) == 10
    assert 'index' in saved_df.columns

def test_save_metadata(temp_dir, sample_raw_pool, sample_config):
    """Test saving metadata to JSON."""
    df = load_data(sample_raw_pool)
    test_df, _ = create_test_set(df, sample_config)
    
    output_path = Path(temp_dir) / "metadata.json"
    save_metadata(test_df, str(output_path))
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        meta = json.load(f)
    
    assert 'row_count' in meta
    assert meta['row_count'] == 10
    assert 'checksum' in meta
    assert 'formation_energy_stats' in meta