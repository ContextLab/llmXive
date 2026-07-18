import os
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path
import networkx as nx
import mne
import mne.io

from data.quality_control import (
    calculate_snr,
    check_graph_connectivity,
    run_qc_for_subject,
    calculate_pipeline_completeness,
    CHANNEL_REMOVAL_THRESHOLD,
    MIN_CHANNELS_REQUIRED,
    MIN_NODES_REQUIRED
)
from config import get_data_root

@pytest.fixture
def temp_data_root():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create necessary directories
        (root / 'processed' / 'eeg').mkdir(parents=True)
        (root / 'processed' / 'connectomes').mkdir(parents=True)
        (root / 'results').mkdir(parents=True)
        yield root

def test_calculate_snr_with_clean_signal():
    """Test SNR calculation with a clean sine wave signal."""
    sampling_rate = 250
    duration = 10  # seconds
    n_times = sampling_rate * duration
    n_channels = 32
    
    # Create a clean sine wave (5 Hz)
    t = np.linspace(0, duration, n_times)
    signal = np.sin(2 * np.pi * 5 * t)
    eeg_data = np.tile(signal, (n_channels, 1))
    
    snr = calculate_snr(eeg_data, sampling_rate)
    
    # Clean signal should have high SNR
    assert snr > 0, "Clean signal should have positive SNR"
    assert isinstance(snr, float), "SNR should be a float"

def test_calculate_snr_with_noisy_signal():
    """Test SNR calculation with a noisy signal."""
    sampling_rate = 250
    duration = 10
    n_times = sampling_rate * duration
    n_channels = 32
    
    # Create a signal with noise
    t = np.linspace(0, duration, n_times)
    signal = np.sin(2 * np.pi * 5 * t)
    noise = np.random.randn(n_times) * 0.5
    noisy_signal = signal + noise
    eeg_data = np.tile(noisy_signal, (n_channels, 1))
    
    snr = calculate_snr(eeg_data, sampling_rate)
    
    # Noisy signal should have lower SNR than clean signal
    assert isinstance(snr, float), "SNR should be a float"

def test_calculate_snr_empty_data():
    """Test SNR calculation with empty data."""
    eeg_data = np.array([])
    snr = calculate_snr(eeg_data, 250)
    assert snr == 0.0, "Empty data should return 0 SNR"

def test_check_graph_connectivity_connected():
    """Test graph connectivity check with a connected graph."""
    # Create a fully connected graph
    n_nodes = 10
    adjacency_matrix = np.ones((n_nodes, n_nodes))
    np.fill_diagonal(adjacency_matrix, 0)
    
    is_connected, density = check_graph_connectivity(adjacency_matrix)
    
    assert is_connected, "Fully connected graph should be connected"
    assert density == 1.0, "Fully connected graph should have density 1.0"

def test_check_graph_connectivity_disconnected():
    """Test graph connectivity check with a disconnected graph."""
    # Create a disconnected graph (two separate components)
    n_nodes = 10
    adjacency_matrix = np.zeros((n_nodes, n_nodes))
    
    # Connect nodes 0-4 to each other
    for i in range(5):
        for j in range(5):
            if i != j:
                adjacency_matrix[i, j] = 1
    
    is_connected, density = check_graph_connectivity(adjacency_matrix)
    
    assert not is_connected, "Disconnected graph should not be connected"
    assert density < 1.0, "Disconnected graph should have density < 1.0"

def test_check_graph_connectivity_empty():
    """Test graph connectivity check with empty matrix."""
    adjacency_matrix = np.array([])
    is_connected, density = check_graph_connectivity(adjacency_matrix)
    
    assert not is_connected, "Empty graph should not be connected"
    assert density == 0.0, "Empty graph should have density 0.0"

def test_run_qc_for_subject_with_valid_data(temp_data_root):
    """Test QC for a subject with valid EEG and dMRI data."""
    subject_id = "sub-001"
    
    # Create valid EEG data
    eeg_dir = temp_data_root / 'processed' / 'eeg' / subject_id
    eeg_dir.mkdir(parents=True)
    
    # Create a simple FIF file with dummy data
    info = mne.create_info(ch_names=[f'EEG {i:03d}' for i in range(32)], 
                           sfreq=250, ch_types='eeg')
    data = np.random.randn(32, 2500)  # 10 seconds of data
    raw = mne.io.RawArray(data, info)
    raw.save(str(eeg_dir / 'eeg_cleaned.fif'), overwrite=True)
    
    # Create valid connectome data
    connectome_dir = temp_data_root / 'processed' / 'connectomes' / subject_id
    connectome_dir.mkdir(parents=True)
    
    # Create a connected graph
    adjacency_matrix = np.random.rand(20, 20)
    adjacency_matrix = (adjacency_matrix + adjacency_matrix.T) / 2
    np.fill_diagonal(adjacency_matrix, 0)
    np.save(str(connectome_dir / 'connectome.npy'), adjacency_matrix)
    
    # Run QC
    result = run_qc_for_subject(subject_id, temp_data_root)
    
    assert result['subject_id'] == subject_id
    assert result['eeg_qc_passed'] is True
    assert result['dMRI_qc_passed'] is True
    assert result['pipeline_complete'] is True
    assert len(result['reasons']) == 0

def test_run_qc_for_subject_missing_eeg(temp_data_root):
    """Test QC for a subject with missing EEG data."""
    subject_id = "sub-002"
    
    # Create only connectome data
    connectome_dir = temp_data_root / 'processed' / 'connectomes' / subject_id
    connectome_dir.mkdir(parents=True)
    
    adjacency_matrix = np.random.rand(20, 20)
    np.save(str(connectome_dir / 'connectome.npy'), adjacency_matrix)
    
    # Run QC
    result = run_qc_for_subject(subject_id, temp_data_root)
    
    assert result['eeg_qc_passed'] is False
    assert result['dMRI_qc_passed'] is True
    assert result['pipeline_complete'] is False
    assert any('EEG file not found' in reason for reason in result['reasons'])

def test_run_qc_for_subject_disconnected_graph(temp_data_root):
    """Test QC for a subject with a disconnected structural graph."""
    subject_id = "sub-003"
    
    # Create valid EEG data
    eeg_dir = temp_data_root / 'processed' / 'eeg' / subject_id
    eeg_dir.mkdir(parents=True)
    
    info = mne.create_info(ch_names=[f'EEG {i:03d}' for i in range(32)], 
                           sfreq=250, ch_types='eeg')
    data = np.random.randn(32, 2500)
    raw = mne.io.RawArray(data, info)
    raw.save(str(eeg_dir / 'eeg_cleaned.fif'), overwrite=True)
    
    # Create a disconnected connectome
    connectome_dir = temp_data_root / 'processed' / 'connectomes' / subject_id
    connectome_dir.mkdir(parents=True)
    
    # Create two separate components
    adjacency_matrix = np.zeros((20, 20))
    for i in range(10):
        for j in range(10):
            if i != j:
                adjacency_matrix[i, j] = 1
    
    np.save(str(connectome_dir / 'connectome.npy'), adjacency_matrix)
    
    # Run QC
    result = run_qc_for_subject(subject_id, temp_data_root)
    
    assert result['eeg_qc_passed'] is True
    assert result['dMRI_qc_passed'] is False
    assert result['pipeline_complete'] is False
    assert any('Disconnected structural graph' in reason for reason in result['reasons'])

def test_calculate_pipeline_completeness(temp_data_root):
    """Test pipeline completeness calculation."""
    # Create 3 subjects: 2 complete, 1 incomplete
    for i in range(1, 4):
        subject_id = f"sub-{i:03d}"
        
        # Create EEG data for all
        eeg_dir = temp_data_root / 'processed' / 'eeg' / subject_id
        eeg_dir.mkdir(parents=True)
        
        info = mne.create_info(ch_names=[f'EEG {j:03d}' for j in range(32)], 
                               sfreq=250, ch_types='eeg')
        data = np.random.randn(32, 2500)
        raw = mne.io.RawArray(data, info)
        raw.save(str(eeg_dir / 'eeg_cleaned.fif'), overwrite=True)
        
        # Create connectome data
        connectome_dir = temp_data_root / 'processed' / 'connectomes' / subject_id
        connectome_dir.mkdir(parents=True)
        
        if i == 3:
            # Create disconnected graph for subject 3
            adjacency_matrix = np.zeros((20, 20))
            for j in range(10):
                for k in range(10):
                    if j != k:
                        adjacency_matrix[j, k] = 1
        else:
            # Create connected graph for subjects 1 and 2
            adjacency_matrix = np.random.rand(20, 20)
            adjacency_matrix = (adjacency_matrix + adjacency_matrix.T) / 2
            np.fill_diagonal(adjacency_matrix, 0)
        
        np.save(str(connectome_dir / 'connectome.npy'), adjacency_matrix)
    
    # Calculate completeness
    completion_rate, qc_results = calculate_pipeline_completeness(temp_data_root)
    
    assert len(qc_results) == 3
    assert completion_rate == pytest.approx(2/3, rel=0.01)
    
    # Check that report files were created
    assert (temp_data_root / 'results' / 'qc_detailed_report.csv').exists()
    assert (temp_data_root / 'results' / 'qc_summary.json').exists()

def test_calculate_pipeline_completeness_no_data(temp_data_root):
    """Test pipeline completeness with no data."""
    completion_rate, qc_results = calculate_pipeline_completeness(temp_data_root)
    
    assert completion_rate == 0.0
    assert len(qc_results) == 0