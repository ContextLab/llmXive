import pytest
import sys
import os
import logging
import yaml

# Ensure code directory is in path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = os.path.join(os.path.dirname(__file__), '..', 'code')
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    yield
    if code_dir in sys.path:
        sys.path.remove(code_dir)

@pytest.fixture(autouse=True)
def setup_test_logging():
    """Configure logging for tests to prevent noise in output unless explicitly needed."""
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    yield

@pytest.fixture
def project_root():
    """Return the absolute path to the project root."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def data_dir(project_root):
    """Return the path to the data directory."""
    return os.path.join(project_root, 'data')

@pytest.fixture
def synthetic_data_dir(data_dir):
    """Return the path to the synthetic data directory."""
    path = os.path.join(data_dir, 'synthetic')
    os.makedirs(path, exist_ok=True)
    return path

@pytest.fixture
def processed_data_dir(data_dir):
    """Return the path to the processed data directory."""
    path = os.path.join(data_dir, 'processed')
    os.makedirs(path, exist_ok=True)
    return path

@pytest.fixture
def protocols_dir(data_dir):
    """Return the path to the protocols directory."""
    path = os.path.join(data_dir, 'protocols')
    os.makedirs(path, exist_ok=True)
    return path

@pytest.fixture
def protocol_yaml(protocols_dir):
    """Return the path to the protocol.yaml file."""
    return os.path.join(protocols_dir, 'protocol.yaml')

@pytest.fixture
def contracts_dir(project_root):
    """Return the path to the contracts directory."""
    path = os.path.join(project_root, 'contracts')
    os.makedirs(path, exist_ok=True)
    return path

@pytest.fixture
def results_dir(project_root):
    """Return the path to the results directory."""
    path = os.path.join(project_root, 'results')
    os.makedirs(path, exist_ok=True)
    return path

@pytest.fixture
def models_dir(results_dir):
    """Return the path to the models directory."""
    path = os.path.join(results_dir, 'models')
    os.makedirs(path, exist_ok=True)
    return path

@pytest.fixture
def reports_dir(results_dir):
    """Return the path to the reports directory."""
    path = os.path.join(results_dir, 'reports')
    os.makedirs(path, exist_ok=True)
    return path

@pytest.fixture
def ethics_dir(data_dir):
    """Return the path to the ethics directory."""
    path = os.path.join(data_dir, 'ethics')
    os.makedirs(path, exist_ok=True)
    return path

@pytest.fixture
def raw_data_dir(data_dir):
    """Return the path to the raw data directory."""
    path = os.path.join(data_dir, 'raw')
    os.makedirs(path, exist_ok=True)
    return path
