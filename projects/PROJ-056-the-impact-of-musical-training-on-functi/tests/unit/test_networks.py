import os
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.networks import (
    load_connectivity_matrices,
    load_atlas_annotations,
    get_roi_indices_for_networks,
    extract_network_metrics,
    process_network_extraction
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_connectivity_data(temp_dirs):
    """Generate mock connectivity matrices."""
    n_subjects = 10
    n_rois = 100
    data = np.random.rand(n_subjects, n_rois, n_rois).astype(np.float32)
    # Symmetrize
    data = (data + data.transpose(0, 2, 1)) / 2
    
    filepath = temp_dirs / "connectivity_test.npy"
    np.save(filepath, data)
    return str(filepath)

@pytest.fixture
def mock_atlas_data(temp_dirs):
    """Generate mock atlas parquet file."""
    n_rois = 100
    data = []
    for i in range(n_rois):
        # Assign networks cyclically to ensure all target networks exist
        net = 'Auditory' if i % 3 == 0 else ('Motor' if i % 3 == 1 else 'Executive')
        data.append({'roi_index': i, 'network': net, 'label': f'ROI_{i}'})
    
    df = pd.DataFrame(data)
    filepath = temp_dirs / "atlas_test.parquet"
    df.to_parquet(filepath)
    return str(filepath)

def test_load_connectivity_matrices(mock_connectivity_data):
    """Test loading of connectivity matrices."""
    matrices = load_connectivity_matrices(mock_connectivity_data)
    assert matrices.shape[0] == 10
    assert matrices.shape[1] == 100
    assert matrices.shape[2] == 100
    assert matrices.dtype == np.float32

def test_load_atlas_annotations(mock_atlas_data):
    """Test loading of atlas annotations."""
    df = load_atlas_annotations(mock_atlas_data)
    assert 'roi_index' in df.columns
    assert 'network' in df.columns
    assert len(df) == 100

def test_get_roi_indices_for_networks(mock_atlas_data):
    """Test extraction of ROI indices for specific networks."""
    df = load_atlas_annotations(mock_atlas_data)
    indices = get_roi_indices_for_networks(df, ['Auditory', 'Motor'])
    
    # Check that indices are unique and sorted
    assert indices == sorted(list(set(indices)))
    # Check counts (approximate)
    assert len(indices) > 0
    # Ensure only Auditory and Motor indices are returned
    for idx in indices:
        row = df[df['roi_index'] == idx].iloc[0]
        assert row['network'] in ['Auditory', 'Motor']

def test_extract_network_metrics(mock_connectivity_data, mock_atlas_data, temp_dirs):
    """Test the full extraction pipeline and output file content."""
    output_path = str(temp_dirs / "network_metrics_test.csv")
    
    matrices = load_connectivity_matrices(mock_connectivity_data)
    atlas_df = load_atlas_annotations(mock_atlas_data)
    
    target_networks = ['Auditory', 'Motor', 'Executive']
    
    df_result = extract_network_metrics(matrices, atlas_df, target_networks, output_path)
    
    # Verify file exists
    assert os.path.exists(output_path)
    
    # Verify content
    assert 'subject_id' in df_result.columns
    assert 'roi_i' in df_result.columns
    assert 'roi_j' in df_result.columns
    assert 'network_i' in df_result.columns
    assert 'network_j' in df_result.columns
    assert 'connectivity' in df_result.columns
    
    # Verify only target networks are present
    all_networks = set(df_result['network_i'].unique()) | set(df_result['network_j'].unique())
    assert all_networks.issubset(set(target_networks)), f"Found unexpected networks: {all_networks - set(target_networks)}"
    
    # Verify upper triangle only (i < j)
    assert (df_result['roi_i'] < df_result['roi_j']).all()

def test_process_network_extraction(mock_connectivity_data, mock_atlas_data, temp_dirs):
    """Test the high-level process function."""
    output_path = str(temp_dirs / "processed_metrics.csv")
    
    config = {
        'connectivity_path': mock_connectivity_data,
        'atlas_path': mock_atlas_data,
        'output_path': output_path,
        'target_networks': ['Auditory', 'Motor', 'Executive']
    }
    
    df = process_network_extraction(config)
    
    assert df is not None
    assert len(df) > 0
    assert os.path.exists(output_path)
    assert 'connectivity' in df.columns