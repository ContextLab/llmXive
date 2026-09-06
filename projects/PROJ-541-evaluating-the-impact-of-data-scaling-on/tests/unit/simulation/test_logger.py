"""Unit tests for the logger module."""
import pytest
import json
from simulation.logger import setup_logger, inject_batch_context, LogEntry, ReproducibilityLogger
from simulation.schema import save_seed_config, load_seed_config, validate_seed_config, SEED_CONFIG_PATH
import os
import tempfile
from pathlib import Path

def test_setup_logger_returns_instance():
    """Test that setup_logger returns a ReproducibilityLogger instance."""
    logger = setup_logger("test_name")
    assert isinstance(logger, ReproducibilityLogger)
    assert logger.name == "test_name"

def test_setup_logger_with_batch_id_and_seed():
    """Test that setup_logger can inject batch context immediately."""
    logger = setup_logger(batch_id="batch_1", seed=42)
    assert logger._batch_id == "batch_1"
    assert logger._seed == 42

def test_setup_logger_with_none():
    """Test that setup_logger handles None gracefully."""
    logger = setup_logger(None)
    assert logger.name == "reproducibility"

def test_log_entry_creation():
    """Test that LogEntry is created correctly."""
    entry = LogEntry(operation="test_op", parameters={"key": "value"})
    assert entry.operation == "test_op"
    assert entry.parameters == {"key": "value"}
    assert entry.timestamp is not None

def test_log_entry_to_json():
    """Test that LogEntry.to_json() produces valid JSON."""
    entry = LogEntry(operation="test", batch_id="batch_1", seed=42)
    json_str = entry.to_json()
    parsed = json.loads(json_str)
    assert parsed["operation"] == "test"
    assert parsed["batch_id"] == "batch_1"
    assert parsed["seed"] == 42

def test_logger_log_method():
    """Test that logger.log() creates and returns LogEntry."""
    logger = setup_logger("test")
    entry = logger.log("operation_name", param1="value1")
    assert isinstance(entry, LogEntry)
    assert entry.operation == "operation_name"
    assert entry.parameters["param1"] == "value1"

def test_inject_batch_context():
    """Test that inject_batch_context updates logger state."""
    logger = setup_logger("test")
    assert logger._batch_id is None
    assert logger._seed is None

    inject_batch_context(logger, "batch_123", 12345)
    assert logger._batch_id == "batch_123"
    assert logger._seed == 12345

def test_log_with_batch_context():
    """Test that log entries include batch context after injection."""
    logger = setup_logger("test")
    inject_batch_context(logger, "batch_999", 99999)
    
    entry = logger.log("test_operation")
    assert entry.batch_id == "batch_999"
    assert entry.seed == 99999

def test_logger_tolerates_any_call():
    """Test that logger tolerates any call shape without raising."""
    logger = setup_logger("test")
    
    # These should not raise
    logger.info("info message")
    logger.debug("debug message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")
    logger.nonexistent_method()
    
    # Should still work normally
    entry = logger.log("normal_log")
    assert entry is not None

def test_save_seed_config_creates_file():
    """Test that save_seed_config creates the seed_config.json file."""
    # Use a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily override the path
        import simulation.schema as schema_module
        original_path = schema_module.SEED_CONFIG_PATH
        temp_path = Path(tmpdir) / "seed_config.json"
        schema_module.SEED_CONFIG_PATH = temp_path
        
        try:
            # Remove if exists
            if temp_path.exists():
                temp_path.unlink()
            
            # Save a seed config
            save_seed_config("batch_test", 12345, "a" * 64)
            
            # Check file exists
            assert temp_path.exists()
            
            # Check content
            with open(temp_path, 'r') as f:
                config = json.load(f)
            
            assert "batch_test" in config
            assert config["batch_test"]["seed"] == 12345
            assert config["batch_test"]["config_hash"] == "a" * 64
            assert "timestamp" in config["batch_test"]
        finally:
            # Restore original path
            schema_module.SEED_CONFIG_PATH = original_path

def test_save_seed_config_append_only():
    """Test that save_seed_config appends without overwriting."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import simulation.schema as schema_module
        original_path = schema_module.SEED_CONFIG_PATH
        temp_path = Path(tmpdir) / "seed_config.json"
        schema_module.SEED_CONFIG_PATH = temp_path
        
        try:
            # Save first entry
            save_seed_config("batch_1", 111, "a" * 64)
            
            # Save second entry
            save_seed_config("batch_2", 222, "b" * 64)
            
            # Check both exist
            config = load_seed_config()
            assert "batch_1" in config
            assert "batch_2" in config
            assert config["batch_1"]["seed"] == 111
            assert config["batch_2"]["seed"] == 222
            
            # Try to overwrite batch_1 (should not change)
            save_seed_config("batch_1", 999, "c" * 64)
            
            config = load_seed_config()
            assert config["batch_1"]["seed"] == 111  # Still 111, not 999
        finally:
            schema_module.SEED_CONFIG_PATH = original_path

def test_validate_seed_config_valid():
    """Test validation of a valid seed config."""
    valid_config = {
        "batch_1": {
            "seed": 123,
            "timestamp": "2024-01-01T00:00:00",
            "config_hash": "a" * 64
        }
    }
    assert validate_seed_config(valid_config) is True

def test_validate_seed_config_invalid_missing_field():
    """Test validation fails on missing required field."""
    invalid_config = {
        "batch_1": {
            "seed": 123,
            "timestamp": "2024-01-01T00:00:00"
            # Missing config_hash
        }
    }
    assert validate_seed_config(invalid_config) is False

def test_validate_seed_config_invalid_hash_length():
    """Test validation fails on invalid hash length."""
    invalid_config = {
        "batch_1": {
            "seed": 123,
            "timestamp": "2024-01-01T00:00:00",
            "config_hash": "short"
        }
    }
    assert validate_seed_config(invalid_config) is False

def test_validate_seed_config_invalid_key_format():
    """Test validation fails on invalid batch_id format."""
    invalid_config = {
        "invalid_key": {
            "seed": 123,
            "timestamp": "2024-01-01T00:00:00",
            "config_hash": "a" * 64
        }
    }
    assert validate_seed_config(invalid_config) is False

def test_get_seed_for_batch():
    """Test retrieving seed for a specific batch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import simulation.schema as schema_module
        original_path = schema_module.SEED_CONFIG_PATH
        temp_path = Path(tmpdir) / "seed_config.json"
        schema_module.SEED_CONFIG_PATH = temp_path
        
        try:
            save_seed_config("batch_target", 555, "a" * 64)
            
            seed = schema_module.get_seed_for_batch("batch_target")
            assert seed == 555
            
            # Non-existent batch
            seed = schema_module.get_seed_for_batch("batch_nonexistent")
            assert seed is None
        finally:
            schema_module.SEED_CONFIG_PATH = original_path

def test_log_operation_decorator():
    """Test that log_operation works as a decorator."""
    from simulation.logger import log_operation
    
    @log_operation
    def my_function(x, y):
        return x + y
    
    result = my_function(2, 3)
    assert result == 5

def test_log_operation_direct_call():
    """Test that log_operation works as a direct call."""
    from simulation.logger import log_operation, get_logger
    
    entry = log_operation("test_op", param="value")
    assert isinstance(entry, LogEntry)
    assert entry.operation == "test_op"
    assert entry.parameters["param"] == "value"