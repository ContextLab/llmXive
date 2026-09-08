import os
import sys
import json
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the code directory to the path for imports
@pytest.fixture(autouse=True)
def setup_code_path():
    """Ensure the code directory is in the Python path."""
    code_dir = Path(__file__).parent.parent / 'code'
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration with temporary directories."""
    config_data = {
        'DATA_RAW_DIR': str(tmp_path / 'data' / 'raw'),
        'DATA_PROCESSED_DIR': str(tmp_path / 'data' / 'processed'),
        'DATA_LOGS_DIR': str(tmp_path / 'data' / 'logs'),
        'RESULTS_DIR': str(tmp_path / 'results'),
        'FIGURES_DIR': str(tmp_path / 'figures'),
        'DOCS_DIR': str(tmp_path / 'docs'),
        'STATE_DIR': str(tmp_path / 'state'),
        'SEED': 42,
        'N_MOTIF_NODES': 3,
        'EXPECTED_COHORT_SIZE': 10,
        'ALPHA': 0.05,
        'PERMUTATIONS': 1000,
        'VIF_THRESHOLD': 5.0
    }
    
    # Create directories
    for dir_path in [
        config_data['DATA_RAW_DIR'],
        config_data['DATA_PROCESSED_DIR'],
        config_data['DATA_LOGS_DIR'],
        config_data['RESULTS_DIR'],
        config_data['FIGURES_DIR'],
        config_data['DOCS_DIR'],
        config_data['STATE_DIR']
    ]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create a mock checksums file
    checksums_file = Path(config_data['DATA_RAW_DIR']) / '.checksums.json'
    with open(checksums_file, 'w') as f:
        json.dump({}, f)

    # Create a mock subject list manifest
    manifest_file = Path(config_data['DATA_PROCESSED_DIR']) / 'subject_list_manifest.json'
    with open(manifest_file, 'w') as f:
        json.dump({
            "total_subjects": config_data['EXPECTED_COHORT_SIZE'],
            "subject_ids": [f"100{str(i).zfill(3)}" for i in range(config_data['EXPECTED_COHORT_SIZE'])],
            "subjects_attempted": config_data['EXPECTED_COHORT_SIZE']
        }, f)
    
    # Create a mock structural connectome metadata file
    metadata_file = Path(config_data['DATA_PROCESSED_DIR']) / 'structural_connectome_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump({
            "subjects": {f"100{str(i).zfill(3)}": "complete" for i in range(config_data['EXPECTED_COHORT_SIZE'])}
        }, f)

    # Create a mock global efficiency file
    eff_file = Path(config_data['DATA_PROCESSED_DIR']) / 'global_efficiency.json'
    with open(eff_file, 'w') as f:
        json.dump([
            {"subject_id": f"100{str(i).zfill(3)}", "global_efficiency": 0.5 + (i * 0.01)}
            for i in range(config_data['EXPECTED_COHORT_SIZE'])
        ], f)

    # Patch the config module with these values
    with patch('config.DATA_RAW_DIR', config_data['DATA_RAW_DIR']):
        with patch('config.DATA_PROCESSED_DIR', config_data['DATA_PROCESSED_DIR']):
            with patch('config.DATA_LOGS_DIR', config_data['DATA_LOGS_DIR']):
                with patch('config.RESULTS_DIR', config_data['RESULTS_DIR']):
                    with patch('config.FIGURES_DIR', config_data['FIGURES_DIR']):
                        with patch('config.DOCS_DIR', config_data['DOCS_DIR']):
                            with patch('config.STATE_DIR', config_data['STATE_DIR']):
                                with patch('config.SEED', config_data['SEED']):
                                    with patch('config.N_MOTIF_NODES', config_data['N_MOTIF_NODES']):
                                        with patch('config.EXPECTED_COHORT_SIZE', config_data['EXPECTED_COHORT_SIZE']):
                                            with patch('config.ALPHA', config_data['ALPHA']):
                                                with patch('config.PERMUTATIONS', config_data['PERMUTATIONS']):
                                                    with patch('config.VIF_THRESHOLD', config_data['VIF_THRESHOLD']):
                                                        yield config_data

@pytest.fixture
def mock_logger(tmp_path):
    """Create a mock logger that writes to a file."""
    log_file = tmp_path / 'test.log'
    
    with patch('utils.get_logger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_logger.info = lambda msg: log_file.write(f"INFO: {msg}\n")
        mock_logger.warning = lambda msg: log_file.write(f"WARNING: {msg}\n")
        mock_logger.error = lambda msg: log_file.write(f"ERROR: {msg}\n")
        mock_logger.debug = lambda msg: log_file.write(f"DEBUG: {msg}\n")
        mock_get_logger.return_value = mock_logger
        yield mock_logger

@pytest.fixture
def sample_binary_adjacency():
    """Create a sample binary adjacency matrix for testing."""
    adj = np.array([
        [0, 1, 1, 0, 1],
        [1, 0, 1, 1, 0],
        [1, 1, 0, 1, 1],
        [0, 1, 1, 0, 1],
        [1, 0, 1, 1, 0]
    ], dtype=float)
    return adj

@pytest.fixture
def sample_weighted_adjacency():
    """Create a sample weighted adjacency matrix for testing."""
    adj = np.array([
        [0, 2.5, 3.1, 0, 1.8],
        [2.5, 0, 4.2, 3.7, 0],
        [3.1, 4.2, 0, 2.9, 5.1],
        [0, 3.7, 2.9, 0, 4.0],
        [1.8, 0, 5.1, 4.0, 0]
    ], dtype=float)
    return adj

@pytest.fixture
def sample_bold_data():
    """Create sample BOLD time series data."""
    # Shape: (time_points, regions)
    n_timepoints = 200
    n_regions = 10
    np.random.seed(42)
    bold_data = np.random.randn(n_timepoints, n_regions)
    return bold_data

@pytest.fixture
def mock_hcp_access():
    """Mock HCP S3 access to avoid actual AWS calls."""
    with patch('download.boto3.client') as mock_boto:
        mock_client = MagicMock()
        mock_client.head_object.return_value = {'ContentLength': 100}
        mock_boto.return_value = mock_client
        yield mock_client