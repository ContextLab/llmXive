import os
import json
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from download import download_subject_data, process_subjects
from preprocess import process_connectome, main as preprocess_main
from motifs import process_motif_analysis, main as motifs_main
from stats import main as stats_main
from report import main as report_main

@pytest.fixture
def mock_pipeline_dirs(tmp_path):
    """Set up mock directory structure for pipeline testing."""
    dirs = {
        'raw': tmp_path / 'data' / 'raw',
        'processed': tmp_path / 'data' / 'processed',
        'logs': tmp_path / 'data' / 'logs',
        'results': tmp_path / 'results',
        'figures': tmp_path / 'figures',
        'docs': tmp_path / 'docs'
    }
    
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create mock checksums file
    checksums = {
        "sub-123_dwi.trk": "abc123def456",
        "sub-123_rsfmri.nii.gz": "def456abc123"
    }
    with open(dirs['raw'] / '.checksums.json', 'w') as f:
        json.dump(checksums, f)
    
    return dirs

@pytest.fixture
def mock_subject_data(mock_pipeline_dirs):
    """Create mock subject data files."""
    raw_dir = mock_pipeline_dirs['raw']
    
    # Create dummy DWI file
    dwi_path = raw_dir / "sub-123_dwi.trk"
    dwi_path.touch()
    
    # Create dummy rs-fMRI file
    rsfmri_path = raw_dir / "sub-123_rsfmri.nii.gz"
    rsfmri_path.touch()
    
    # Create dummy atlas
    atlas_path = raw_dir / "atlas.nii.gz"
    atlas_path.touch()
    
    return {
        'dwi_path': str(dwi_path),
        'rsfmri_path': str(rsfmri_path),
        'atlas_path': str(atlas_path)
    }

def test_end_to_end_pipeline_creates_processed_files(mock_pipeline_dirs, mock_subject_data):
    """Contract: Run end-end on mock subjects; assert data/processed/ contains structural.npy and rsfc.npy."""
    # Mock the download and processing functions
    with patch('download.download_subject_data') as mock_download:
        mock_download.return_value = {
            'dwi_path': mock_subject_data['dwi_path'],
            'rsfmri_path': mock_subject_data['rsfmri_path']
        }
        
        # Mock streamlines and atlas loading
        with patch('preprocess.load_streamlines') as mock_streamlines:
            mock_streamlines.return_value = [
                np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]], dtype=float)
            ]
            
            with patch('preprocess.load_atlas') as mock_atlas:
                atlas_data = np.zeros((10, 10, 10), dtype=np.int16)
                atlas_data[0:2, :, :] = 1
                atlas_data[2:4, :, :] = 2
                mock_img = MagicMock()
                mock_img.get_fdata.return_value = atlas_data
                mock_atlas.return_value = mock_img
                
                # Mock networkx for efficiency calculation
                with patch('preprocess.networkx.from_numpy_array') as mock_nx:
                    mock_graph = MagicMock()
                    mock_graph.number_of_nodes.return_value = 2
                    mock_graph.number_of_edges.return_value = 1
                    mock_nx.return_value = mock_graph
                    
                    with patch('preprocess.networkx.global_efficiency') as mock_eff:
                        mock_eff.return_value = 0.5
                        
                        # Run the preprocessing pipeline
                        with patch('config.DATA_RAW_DIR', str(mock_pipeline_dirs['raw'])):
                            with patch('config.DATA_PROCESSED_DIR', str(mock_pipeline_dirs['processed'])):
                                with patch('config.DATA_LOGS_DIR', str(mock_pipeline_dirs['logs'])):
                                    preprocess_main()
                    
                    # Check that output files were created
                    processed_dir = mock_pipeline_dirs['processed']
                    
                    assert (processed_dir / 'weighted_adjacency.npy').exists()
                    assert (processed_dir / 'canonical_binary_adj.npy').exists()
                    assert (processed_dir / 'rsfc.npy').exists()
                    assert (processed_dir / 'global_efficiency.json').exists()
                    
                    # Verify file contents
                    weighted_adj = np.load(processed_dir / 'weighted_adjacency.npy')
                    assert isinstance(weighted_adj, np.ndarray)
                    assert weighted_adj.shape[0] == weighted_adj.shape[1]
                    
                    binary_adj = np.load(processed_dir / 'canonical_binary_adj.npy')
                    assert isinstance(binary_adj, np.ndarray)
                    assert np.all((binary_adj == 0) | (binary_adj == 1))
                    
                    rsfc = np.load(processed_dir / 'rsfc.npy')
                    assert isinstance(rsfc, np.ndarray)
                    
                    with open(processed_dir / 'global_efficiency.json', 'r') as f:
                        eff_data = json.load(f)
                        assert 'subject_id' in eff_data
                        assert 'global_efficiency' in eff_data

def test_end_to_end_pipeline_logs_success(mock_pipeline_dirs, mock_subject_data):
    """Contract: Assert data/logs/pipeline.log contains 'Processed all subjects' without errors."""
    with patch('download.download_subject_data') as mock_download:
        mock_download.return_value = {
            'dwi_path': mock_subject_data['dwi_path'],
            'rsfmri_path': mock_subject_data['rsfmri_path']
        }
        
        with patch('preprocess.load_streamlines') as mock_streamlines:
            mock_streamlines.return_value = [
                np.array([[0, 0, 0], [1, 1, 1], [2, 2, 2]], dtype=float)
            ]
            
            with patch('preprocess.load_atlas') as mock_atlas:
                atlas_data = np.zeros((10, 10, 10), dtype=np.int16)
                atlas_data[0:2, :, :] = 1
                mock_img = MagicMock()
                mock_img.get_fdata.return_value = atlas_data
                mock_atlas.return_value = mock_img
                
                with patch('preprocess.networkx.from_numpy_array') as mock_nx:
                    mock_graph = MagicMock()
                    mock_graph.number_of_nodes.return_value = 2
                    mock_graph.number_of_edges.return_value = 1
                    mock_nx.return_value = mock_graph
                    
                    with patch('preprocess.networkx.global_efficiency') as mock_eff:
                        mock_eff.return_value = 0.5
                        
                        with patch('config.DATA_RAW_DIR', str(mock_pipeline_dirs['raw'])):
                            with patch('config.DATA_PROCESSED_DIR', str(mock_pipeline_dirs['processed'])):
                                with patch('config.DATA_LOGS_DIR', str(mock_pipeline_dirs['logs'])):
                                    preprocess_main()
                    
                    # Check log file
                    log_file = mock_pipeline_dirs['logs'] / 'pipeline.log'
                    
                    assert log_file.exists()
                    
                    with open(log_file, 'r') as f:
                        log_content = f.read()
                    
                    assert 'Processed all subjects' in log_content
                    assert 'ERROR' not in log_content
