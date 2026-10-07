import os
import tempfile
import pytest
import pandas as pd
from code.data.ingest_netflow import (
    normalize_columns,
    load_raw_flows,
    process_scenario,
    write_processed_flows,
    ensure_data_dirs
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_csv_data():
    return """src_ip,dst_ip,packets,timestamp
    192.168.1.1,192.168.1.2,100,1600000000
    192.168.1.2,192.168.1.3,200,1600000001
    10.0.0.1,10.0.0.2,50,1600000002
    """

@pytest.fixture
def sample_csv_path(temp_dir, sample_csv_data):
    path = os.path.join(temp_dir, "test_scenario.csv")
    with open(path, 'w') as f:
        f.write(sample_csv_data)
    return path

def test_normalize_columns_standard():
    """Test normalization with standard column names."""
    df = pd.DataFrame({
        'src_ip': ['1.1.1.1'],
        'dst_ip': ['2.2.2.2'],
        'packets': [100],
        'timestamp': [1600000000]
    })
    result = normalize_columns(df)
    assert list(result.columns) == ['src_ip', 'dst_ip', 'packets', 'timestamp']
    assert result['packets'].dtype == 'int64'

def test_normalize_columns_variations():
    """Test normalization with varied column names."""
    df = pd.DataFrame({
        'source_ip': ['1.1.1.1'],
        'Dest_IP': ['2.2.2.2'],
        'pkt_count': [100],
        'ts': [1600000000]
    })
    result = normalize_columns(df)
    assert list(result.columns) == ['src_ip', 'dst_ip', 'packets', 'timestamp']

def test_normalize_columns_missing_required():
    """Test that missing required columns raises error."""
    df = pd.DataFrame({
        'src_ip': ['1.1.1.1'],
        'dst_ip': ['2.2.2.2']
    })
    with pytest.raises(ValueError, match="Missing required columns"):
        normalize_columns(df)

def test_load_raw_flows_csv(sample_csv_path, temp_dir):
    """Test loading CSV file."""
    # Copy to expected location for load_raw_flows
    import shutil
    os.makedirs('data/raw', exist_ok=True)
    target_path = os.path.join('data/raw', 'test_load.csv')
    shutil.copy(sample_csv_path, target_path)
    
    try:
        df = load_raw_flows(target_path)
        assert len(df) == 3
        assert 'src_ip' in df.columns
    finally:
        if os.path.exists(target_path):
            os.remove(target_path)
        if os.path.exists('data/raw'):
            os.rmdir('data/raw')

def test_process_scenario(sample_csv_path, temp_dir):
    """Test full scenario processing."""
    import shutil
    os.makedirs('data/processed', exist_ok=True)
    
    try:
        scenario_name, df = process_scenario(sample_csv_path, temp_dir)
        assert scenario_name == "test_scenario"
        assert len(df) == 3
        assert 'timestamp' in df.columns
        assert df['timestamp'].dtype == 'int64'
    finally:
        if os.path.exists('data/processed'):
            shutil.rmtree('data/processed')

def test_write_processed_flows(temp_dir):
    """Test writing to parquet."""
    df = pd.DataFrame({
        'src_ip': ['1.1.1.1'],
        'dst_ip': ['2.2.2.2'],
        'packets': [100],
        'timestamp': [1600000000]
    })
    output_path = os.path.join(temp_dir, "output.parquet")
    write_processed_flows(df, output_path)
    assert os.path.exists(output_path)
    
    # Verify content
    loaded = pd.read_parquet(output_path)
    assert len(loaded) == 1
    assert loaded.iloc[0]['src_ip'] == '1.1.1.1'

def test_ensure_data_dirs(temp_dir):
    """Test directory creation."""
    # Change to temp dir to avoid creating in project root
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        ensure_data_dirs()
        assert os.path.exists('data/raw')
        assert os.path.exists('data/processed')
        assert os.path.exists('data/results')
    finally:
        os.chdir(original_cwd)