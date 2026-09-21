import os
import pytest
from config import get_config, ensure_directories

@pytest.fixture
def config():
    return get_config()

def test_data_raw_exists(config):
    ensure_directories(config)
    assert os.path.exists("data/raw"), "data/raw directory must exist"

def test_data_processed_exists(config):
    ensure_directories(config)
    assert os.path.exists("data/processed"), "data/processed directory must exist"

def test_data_assets_exists(config):
    ensure_directories(config)
    assert os.path.exists("data/assets"), "data/assets directory must exist"

def test_code_dir_exists(config):
    ensure_directories(config)
    assert os.path.exists("code"), "code directory must exist"

def test_artifacts_dir_exists(config):
    ensure_directories(config)
    assert os.path.exists("artifacts"), "artifacts directory must exist"

def test_tests_dir_exists(config):
    ensure_directories(config)
    assert os.path.exists("tests"), "tests directory must exist"

def test_artifacts_logs_exists(config):
    ensure_directories(config)
    assert os.path.exists("artifacts/logs"), "artifacts/logs directory must exist"

def test_artifacts_weights_exists(config):
    ensure_directories(config)
    assert os.path.exists("artifacts/weights"), "artifacts/weights directory must exist"