import os
import pytest
from unittest.mock import patch
from code.setup_env import get_environment_config, apply_seed

@patch.dict(os.environ, {
    'RANDOM_SEED': '123',
    'MODEL_PATH': '/fake/path',
    'MAX_TURNS_PRIMARY': '50',
    'MAX_TURNS_EXTENDED': '1000',
    'DEVICE': 'cpu',
    'DATA_RAW_DIR': 'data/raw',
    'DATA_PROCESSED_DIR': 'data/processed',
    'RESULTS_DIR': 'results',
    'LOG_LEVEL': 'INFO',
    'ORTHOGONALIZATION_THRESHOLD': '0.2'
})
def test_get_environment_config_defaults():
    config = get_environment_config()
    assert config['RANDOM_SEED'] == 123
    assert config['MODEL_PATH'] == '/fake/path'
    assert config['MAX_TURNS_PRIMARY'] == 50
    assert config['MAX_TURNS_EXTENDED'] == 1000
    assert config['DEVICE'] == 'cpu'
    assert config['ORTHOGONALIZATION_THRESHOLD'] == 0.2

@patch.dict(os.environ, {}, clear=True)
def test_get_environment_config_missing_model_path():
    # Set a seed to avoid immediate failure, but leave MODEL_PATH missing
    os.environ['RANDOM_SEED'] = '42'
    with pytest.raises(RuntimeError, match="Missing required environment variable: MODEL_PATH"):
        get_environment_config()

@patch.dict(os.environ, {
    'RANDOM_SEED': 'invalid',
    'MODEL_PATH': '/fake/path'
})
def test_get_environment_config_invalid_seed():
    with pytest.raises(RuntimeError, match="Invalid value for environment variable"):
        get_environment_config()

def test_apply_seed():
    import random
    import numpy as np
    import torch
    
    # Set known seed
    apply_seed(42)
    
    # Verify random
    val1 = random.random()
    apply_seed(42)
    val2 = random.random()
    assert val1 == val2
