import pytest
import sys
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from generation.generator import (
    get_available_memory_gb,
    calculate_batch_size,
    log_batch_reduction,
    log_memory_state,
    get_memory_log_path
)
from utils.logger import initialize_memory_log, get_memory_log

@pytest.fixture
def setup_memory_log():
    """Fixture to initialize memory log for tests."""
    log_path = get_memory_log_path()
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    initialize_memory_log()
    yield
    # Cleanup after test
    if os.path.exists(log_path):
        os.remove(log_path)

def test_get_available_memory_gb(setup_memory_log):
    """Test that available memory is a positive float."""
    mem = get_available_memory_gb()
    assert isinstance(mem, float)
    assert mem > 0

def test_calculate_batch_size_limits(setup_memory_log):
    """Test that batch size is clamped between MIN and MAX."""
    # Mock available memory to be extremely high
    with patch('generation.generator.get_available_memory_gb', return_value=1000.0):
        batch = calculate_batch_size()
        assert batch <= 20 # MAX_BATCH_SIZE
    
    # Mock available memory to be extremely low
    with patch('generation.generator.get_available_memory_gb', return_value=0.001):
        batch = calculate_batch_size()
        assert batch >= 1 # MIN_BATCH_SIZE

def test_log_batch_reduction(setup_memory_log):
    """Test that log_batch_reduction writes to memory_log.json."""
    initialize_memory_log() # Ensure fresh state
    log_batch_reduction(5, "Test Reduction")
    
    log_path = get_memory_log_path()
    assert os.path.exists(log_path)
    
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) > 0
    assert data[-1]['action'] == 'batch_reduction'
    assert data[-1]['batch_size'] == 5
    assert data[-1]['reason'] == 'Test Reduction'

def test_log_memory_state(setup_memory_log):
    """Test that log_memory_state writes correct structure."""
    initialize_memory_log()
    log_memory_state(10, "test_action")
    
    log_path = get_memory_log_path()
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) > 0
    entry = data[-1]
    assert 'timestamp' in entry
    assert entry['action'] == 'test_action'
    assert entry['batch_size'] == 10
    assert 'available_memory_gb' in entry