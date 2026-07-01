import pytest
import os
import tempfile
import mne
import numpy as np
from pathlib import Path
import yaml

from preprocess import run_preprocessing_pipeline, load_config_and_validate

@pytest.fixture
def realistic_test_data():
    """
    Generates a realistic synthetic EEG dataset with events to simulate ds003645.
    """
    sfreq = 500
    n_channels = 32
    ch_names = [f'EEG {i:03d}' for i in range(n_channels)]
    ch_names[0] = 'Fz'
    ch_names[1] = 'FCz'
    ch_names[2] = 'Cz'
    ch_names[3] = 'Pz'
    
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    n_times = 100000 # 200 seconds
    data = np.random.randn(n_channels, n_times) * 1e-6 # Microvolts
    
    raw = mne.io.RawArray(data, info)
    
    # Add stim channel
    stim_data = np.zeros((1, n_times))
    # Create events at 1s, 2s, 3s...
    # 1 = Standard, 2 = Deviant
    events = []
    for i in range(10, 100, 10): # Events every 10 seconds
        stim_data[0, i * sfreq] = 1 if (i % 20 == 0) else 2
        events.append([i * sfreq, 0, 1 if (i % 20 == 0) else 2])
    
    events = np.array(events)
    
    # Add events to raw
    # MNE RawArray doesn't directly support adding events, so we create a new raw with annotations or use mne.add_events
    # Simpler: Save raw, then add events via mne
    with tempfile.NamedTemporaryFile(suffix='.fif', delete=False) as f:
        raw_path = f.name
        raw.save(raw_path, overwrite=True)
    
    raw = mne.io.read_raw_fif(raw_path, preload=True)
    # Create a stim channel manually by adding it to the data
    # This is a bit hacky for testing, but works for integration
    # Better approach: Use mne.make_fake_data or similar, but let's stick to standard MNE
    
    # Re-create with stim channel properly
    ch_names.append('STI 014')
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=['eeg']*32 + ['stim'])
    data = np.zeros((33, n_times))
    data[:32] = np.random.randn(32, n_times) * 1e-6
    
    # Fill stim channel
    for i, event in enumerate(events):
        time_idx = int(event[0])
        if time_idx < n_times:
            data[32, time_idx] = event[2]
    
    raw = mne.io.RawArray(data, info)
    
    return raw, raw_path

def test_full_pipeline_integration(realistic_test_data, temp_output_dir):
    raw, raw_path = realistic_test_data
    
    # Save raw to data/raw structure
    data_raw_dir = os.path.join(temp_output_dir, 'data', 'raw')
    os.makedirs(data_raw_dir, exist_ok=True)
    processed_dir = os.path.join(temp_output_dir, 'data', 'processed')
    os.makedirs(processed_dir, exist_ok=True)
    
    # Save the raw file
    raw_fif_path = os.path.join(data_raw_dir, 'sub-test_sub-test.fif')
    raw.save(raw_fif_path, overwrite=True)
    
    # Create config
    config = {
        'filter': {'low': 1.0, 'high': 30.0},
        'epoch': {'tmin': -0.2, 'tmax': 0.6},
        'ica': {'threshold': 0.8}
    }
    config_path = os.path.join(temp_output_dir, 'config.yaml')
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    
    # Run pipeline
    run_preprocessing_pipeline(
        data_dir=data_raw_dir,
        output_dir=processed_dir,
        config_path=config_path
    )
    
    # Verify output
    output_files = list(Path(processed_dir).glob('*.fif'))
    assert len(output_files) > 0, "No output files generated"
    
    # Check content
    epochs = mne.read_epochs(str(output_files[0]))
    assert 'standard' in epochs.event_id
    assert 'deviant' in epochs.event_id
    assert len(epochs) > 0

# Helper fixture for temp dir
@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir