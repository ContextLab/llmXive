"""
Pytest configuration and fixtures for the llmXive PROJ-118 pipeline.

This file sets up the test environment, including:
- Project root path resolution
- Temporary directories for test outputs
- Mock data fixtures (where real data is not available for unit tests)
- Logging configuration for test runs
"""
import os
import sys
import logging
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any, Optional

import pytest
import numpy as np
import mne

# Add project root to path to ensure imports work correctly
# We assume the project root is the parent of the 'tests' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging for tests to avoid cluttering output unless verbose
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root path."""
    return PROJECT_ROOT


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test artifacts.
    Yields the path, and cleans up after the test.
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture(scope="function")
def mock_config(tmp_path: Path) -> Dict[str, Any]:
    """
    Provide a mock configuration dictionary mimicking code/config.yaml.
    Useful for unit tests that don't need real disk I/O.
    """
    return {
        "pipeline": {
            "filter": {"low": 1.0, "high": 30.0},
            "epoch": {"tmin": -0.2, "tmax": 0.6},
            "ica_threshold": 0.8,
            "montage": "standard_32",
            "reference": "average"
        },
        "paths": {
            "raw": str(tmp_path / "raw"),
            "processed": str(tmp_path / "processed"),
            "results": str(tmp_path / "results")
        }
    }


@pytest.fixture(scope="function")
def mock_raw_data(temp_dir: Path) -> Path:
    """
    Create a minimal mock raw EEG file (.fif) for testing preprocessing logic.
    This avoids the need to download the full OpenNeuro dataset for unit tests.
    Returns the path to the created file.
    """
    # Create necessary directories
    raw_dir = temp_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    file_path = raw_dir / "sub-01_task-auditory_raw.fif"

    # Generate mock data: 10 seconds at 250Hz, 32 channels
    sfreq = 250.0
    n_channels = 32
    n_times = int(10 * sfreq)
    n_events = 100

    # Create channel names (standard 32-channel subset)
    ch_names = [
        "Fp1", "Fp2", "F7", "F3", "Fz", "F4", "F8",
        "FC5", "FC1", "FC2", "FC6",
        "T7", "C3", "Cz", "C4", "T8",
        "CP5", "CP1", "CP2", "CP6",
        "P7", "P3", "Pz", "P4", "P8",
        "O1", "Oz", "O2",
        "M1", "M2", "EKG"
    ][:n_channels]

    # Create info structure
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
    info.set_montage('standard_1020', match_case=False, match_alias=True, on_missing='ignore')

    # Generate random data (simulating EEG)
    data = np.random.randn(n_channels, n_times) * 1e-6  # Volts

    # Create Raw object
    raw = mne.io.RawArray(data, info)
    raw.set_eeg_reference('average')

    # Save to FIF
    raw.save(file_path, overwrite=True)
    logger.info(f"Created mock raw data at {file_path}")

    return file_path


@pytest.fixture(scope="function")
def mock_epochs(temp_dir: Path, mock_raw_data: Path) -> Path:
    """
    Create mock epoched data for testing extraction and stats logic.
    Returns the path to the created epochs file.
    """
    raw_path = mock_raw_data
    processed_dir = temp_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    epochs_path = processed_dir / "sub-01_epo.fif"

    # Load raw
    raw = mne.io.read_raw_fif(raw_path, preload=True)

    # Create mock events: 100 trials, alternating standard/deviant
    events = []
    for i in range(100):
        start_sample = int(i * 2.5 * 250)  # 2.5s intervals
        event_id = 1 if i % 2 == 0 else 2  # 1=standard, 2=deviant
        events.append([start_sample, 0, event_id])
    events = np.array(events)

    # Define event IDs mapping
    event_id_map = {'standard': 1, 'deviant': 2}

    # Epoch data
    epochs = mne.Epochs(
        raw, events, event_id=event_id_map,
        tmin=-0.2, tmax=0.6, baseline=(-0.2, 0),
        reject=None, preload=True
    )

    # Save epochs
    epochs.save(epochs_path, overwrite=True)
    logger.info(f"Created mock epochs at {epochs_path}")

    return epochs_path


@pytest.fixture(scope="function")
def mock_metrics_csv(temp_dir: Path) -> Path:
    """
    Create a mock metrics.csv file for testing stats.py logic.
    Returns the path to the created CSV.
    """
    import pandas as pd

    metrics_dir = temp_dir / "results"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    csv_path = metrics_dir / "metrics.csv"

    data = {
        'participant_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05'],
        'standard_amplitude': [-2.1, -1.8, -2.5, -1.9, -2.2],
        'standard_latency': [180, 175, 190, 185, 178],
        'deviant_amplitude': [-4.5, -5.1, -4.2, -4.8, -5.0],
        'deviant_latency': [195, 200, 188, 192, 198],
        'peak_detected': [True, True, True, True, True],
        'snr': [2.1, 2.5, 1.9, 2.3, 2.4]
    }

    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    logger.info(f"Created mock metrics CSV at {csv_path}")

    return csv_path


@pytest.fixture(scope="function")
def mock_rejected_log(temp_dir: Path) -> Path:
    """
    Create a mock rejected_participants.log file for testing exclusion logic.
    Returns the path to the created log file.
    """
    log_dir = temp_dir / "processed"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "rejected_participants.log"

    with open(log_path, 'w') as f:
        f.write("sub-06\n")
        f.write("sub-09\n")

    logger.info(f"Created mock rejected log at {log_path}")
    return log_path