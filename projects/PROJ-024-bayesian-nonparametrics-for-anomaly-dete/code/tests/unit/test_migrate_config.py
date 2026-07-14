"""
Unit tests for the config migration utility.
"""
import os
import sys
import tempfile
import yaml
from pathlib import Path
import pytest

# Add parent directory to path for imports if running standalone
# In the actual project structure, this would be handled by the test runner
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.migrate_config import load_yaml, save_yaml, DERIVED_KEYS

def test_load_yaml_existing_file():
    """Test loading an existing YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({'key': 'value'}, f)
        temp_path = Path(f.name)
    
    try:
        data = load_yaml(temp_path)
        assert data == {'key': 'value'}
    finally:
        os.unlink(temp_path)

def test_load_yaml_missing_file():
    """Test loading a missing YAML file raises SystemExit."""
    with pytest.raises(SystemExit):
        load_yaml(Path('/nonexistent/path/file.yaml'))

def test_save_yaml_creates_directory():
    """Test that save_yaml creates parent directories if needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_path = Path(tmpdir) / "subdir" / "test.yaml"
        data = {'test': 'data'}
        
        save_yaml(target_path, data)
        
        assert target_path.exists()
        loaded = load_yaml(target_path)
        assert loaded == data

def test_derived_keys_constant():
    """Test that the DERIVED_KEYS constant contains the expected keys."""
    expected_keys = ['dataset_stats', 'inference_results', 'simulation_metrics']
    assert set(DERIVED_KEYS) == set(expected_keys)

def test_migration_logic_simulation():
    """Simulate the migration logic to ensure keys are moved correctly."""
    # Create a mock config with derived keys
    mock_config = {
        'hyperparameters': {'window_size': 50},
        'seeds': {'global_seed': 42},
        'dataset_stats': {'mean': 0.5, 'std': 0.1},
        'inference_results': {'accuracy': 0.95},
        'simulation_metrics': {'snr': 1.2}
    }
    
    # Simulate extraction logic
    migrated = {}
    for key in DERIVED_KEYS:
        if key in mock_config:
            migrated[key] = mock_config.pop(key)
    
    # Verify keys were removed from config
    assert 'dataset_stats' not in mock_config
    assert 'inference_results' not in mock_config
    assert 'simulation_metrics' not in mock_config
    
    # Verify keys were extracted
    assert 'dataset_stats' in migrated
    assert 'inference_results' in migrated
    assert 'simulation_metrics' in migrated
    
    # Verify remaining config only has base keys
    assert set(mock_config.keys()) == {'hyperparameters', 'seeds'}
