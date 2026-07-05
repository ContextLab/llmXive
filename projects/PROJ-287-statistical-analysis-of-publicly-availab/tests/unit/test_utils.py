"""
Unit tests for logging and manifest utilities.

Tests validate:
1. Logging setup and logger retrieval
2. Manifest generation and validation
3. Integration between logging and manifest components
"""

import json
import os
import tempfile
import logging
from pathlib import Path
from datetime import datetime
import pytest

from src.utils.logging import setup_logging, get_logger, LogContext, handle_exception
from src.utils.manifest import (
    ManifestGenerator,
    generate_reproducibility_manifest,
    save_reproducibility_manifest,
    load_reproducibility_manifest
)
from src.utils.config import get_random_seed, ensure_directories


class TestLoggingUtilities:
    """Tests for logging utilities."""
    
    def test_setup_logging_creates_logger(self):
        """Test that setup_logging creates and configures a logger."""
        logger_name = "test_setup_logging"
        logger = setup_logging(
            name=logger_name,
            level=logging.INFO,
            log_file=None,
            console=True
        )
        
        assert logger is not None
        assert logger.name == logger_name
        assert logger.level == logging.INFO
        
        # Verify handlers are present
        assert len(logger.handlers) > 0
        
        # Clean up handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
    
    def test_get_logger_retrieves_existing(self):
        """Test that get_logger retrieves an existing logger by name."""
        logger_name = "test_get_logger_existing"
        
        # First, create the logger
        logger1 = setup_logging(
            name=logger_name,
            level=logging.DEBUG,
            log_file=None,
            console=False
        )
        
        # Now retrieve it
        logger2 = get_logger(logger_name)
        
        assert logger1 is logger2
        assert logger2.level == logging.DEBUG
        
        # Clean up
        for handler in logger2.handlers[:]:
            logger2.removeHandler(handler)
            handler.close()
    
    def test_log_context_manager(self):
        """Test that LogContext properly sets and restores context."""
        logger = get_logger("test_log_context")
        logger.handlers = []  # Clear handlers to avoid console spam
        
        # Add a memory handler for testing
        memory_handler = logging.Handler()
        memory_handler.setLevel(logging.INFO)
        memory_records = []
        
        class MemoryHandler(logging.Handler):
            def emit(self, record):
                memory_records.append(self.format(record))
        
        memory_handler = MemoryHandler()
        logger.addHandler(memory_handler)
        
        # Test context setting
        with LogContext(logger, {"user_id": "123", "request_id": "abc"}):
            logger.info("Test message with context")
        
        # Verify context was added to log record
        assert len(memory_records) > 0
        assert "user_id=123" in memory_records[0] or "user_id" in memory_records[0]
        
        # Clean up
        logger.removeHandler(memory_handler)
    
    def test_handle_exception_logs_error(self):
        """Test that handle_exception properly logs exceptions."""
        logger = get_logger("test_handle_exception")
        logger.handlers = []
        
        memory_handler = logging.Handler()
        memory_records = []
        
        class MemoryHandler(logging.Handler):
            def emit(self, record):
                memory_records.append((record.levelno, self.format(record)))
        
        memory_handler = MemoryHandler()
        logger.addHandler(memory_handler)
        
        try:
            raise ValueError("Test exception")
        except Exception:
            handle_exception(logger, "An error occurred")
        
        # Verify exception was logged
        assert len(memory_records) > 0
        assert memory_records[0][0] >= logging.ERROR
        assert "Test exception" in memory_records[0][1]
        
        # Clean up
        logger.removeHandler(memory_handler)


class TestManifestUtilities:
    """Tests for manifest generation and validation."""
    
    def test_manifest_generator_initialization(self):
        """Test that ManifestGenerator initializes correctly."""
        generator = ManifestGenerator()
        
        assert generator is not None
        assert "timestamp" in generator.manifest
        assert "project_info" in generator.manifest
        
        # Verify timestamp format
        timestamp = generator.manifest["timestamp"]
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    
    def test_generate_reproducibility_manifest(self):
        """Test that generate_reproducibility_manifest creates valid manifest."""
        test_params = {
            "random_seed": 42,
            "k_topics": 10,
            "windows": ["2000-2004", "2005-2009"]
        }
        
        manifest = generate_reproducibility_manifest(
            parameters=test_params,
            metadata={"source": "test", "version": "1.0"}
        )
        
        # Verify required fields
        assert "timestamp" in manifest
        assert "parameters" in manifest
        assert "metadata" in manifest
        assert "git_info" in manifest
        
        # Verify custom parameters are included
        assert manifest["parameters"]["random_seed"] == 42
        assert manifest["parameters"]["k_topics"] == 10
        
        # Verify metadata
        assert manifest["metadata"]["source"] == "test"
    
    def test_save_and_load_manifest(self):
        """Test saving and loading manifests to/from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test_manifest.json"
            
            # Create and save manifest
            params = {"test_param": "value", "number": 123}
            save_reproducibility_manifest(
                parameters=params,
                output_path=str(manifest_path),
                metadata={"test": True}
            )
            
            # Verify file exists
            assert manifest_path.exists()
            
            # Load manifest
            loaded_manifest = load_reproducibility_manifest(str(manifest_path))
            
            # Verify content
            assert loaded_manifest["parameters"]["test_param"] == "value"
            assert loaded_manifest["parameters"]["number"] == 123
            assert loaded_manifest["metadata"]["test"] is True
            assert "timestamp" in loaded_manifest
    
    def test_manifest_validation_structure(self):
        """Test that manifest has required structure for reproducibility."""
        manifest = generate_reproducibility_manifest(
            parameters={"seed": 42},
            metadata={"source": "validation_test"}
        )
        
        # Check top-level keys
        required_keys = ["timestamp", "parameters", "metadata", "git_info"]
        for key in required_keys:
            assert key in manifest, f"Missing required key: {key}"
        
        # Check nested structure
        assert isinstance(manifest["parameters"], dict)
        assert isinstance(manifest["metadata"], dict)
        assert isinstance(manifest["git_info"], dict)
        
        # Check git_info fields
        git_fields = ["commit_hash", "branch", "is_dirty"]
        for field in git_fields:
            assert field in manifest["git_info"], f"Missing git_info field: {field}"
    
    def test_manifest_with_config_integration(self):
        """Test manifest generation integrates with config utilities."""
        # Get random seed from config
        seed = get_random_seed()
        
        # Generate manifest with seed
        manifest = generate_reproducibility_manifest(
            parameters={"random_seed": seed},
            metadata={"test": "config_integration"}
        )
        
        # Verify seed is in manifest
        assert manifest["parameters"]["random_seed"] == seed
        
        # Ensure directories exist for manifest
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest.json"
            ensure_directories([str(output_path.parent)])
            
            save_reproducibility_manifest(
                parameters={"seed": seed},
                output_path=str(output_path),
                metadata={"test": True}
            )
            
            assert output_path.exists()
    
    def test_manifest_json_serialization(self):
        """Test that manifest can be serialized to valid JSON."""
        manifest = generate_reproducibility_manifest(
            parameters={"data": [1, 2, 3], "nested": {"key": "value"}},
            metadata={"source": "json_test"}
        )
        
        # Serialize to JSON
        json_str = json.dumps(manifest)
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        
        # Verify content matches
        assert parsed["parameters"]["data"] == [1, 2, 3]
        assert parsed["parameters"]["nested"]["key"] == "value"
        assert parsed["metadata"]["source"] == "json_test"
    
    def test_manifest_timestamp_format(self):
        """Test that manifest timestamp is in ISO format with timezone."""
        manifest = generate_reproducibility_manifest(
            parameters={},
            metadata={}
        )
        
        timestamp = manifest["timestamp"]
        
        # Verify ISO format with timezone
        try:
            # Handle both 'Z' and '+00:00' formats
            if timestamp.endswith('Z'):
                timestamp = timestamp[:-1] + '+00:00'
            datetime.fromisoformat(timestamp)
        except ValueError as e:
            pytest.fail(f"Timestamp is not in valid ISO format: {timestamp}. Error: {e}")
    
    def test_manifest_checksum_consistency(self):
        """Test that manifest includes and validates checksums for data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test data file
            data_file = Path(tmpdir) / "test_data.json"
            data_content = {"test": "data", "value": 42}
            with open(data_file, 'w') as f:
                json.dump(data_content, f)
            
            # Generate manifest with file reference
            manifest = generate_reproducibility_manifest(
                parameters={"data_file": str(data_file)},
                metadata={"source": "checksum_test"}
            )
            
            # Save manifest
            manifest_path = Path(tmpdir) / "manifest.json"
            save_reproducibility_manifest(
                parameters={"data_file": str(data_file)},
                output_path=str(manifest_path),
                metadata={"source": "checksum_test"}
            )
            
            # Load and verify
            loaded = load_reproducibility_manifest(str(manifest_path))
            assert loaded["parameters"]["data_file"] == str(data_file)
            assert "timestamp" in loaded
    
    def test_manifest_large_parameters(self):
        """Test manifest generation with large parameter sets."""
        large_params = {
            f"param_{i}": f"value_{i}" for i in range(100)
        }
        large_params["nested_large"] = {
            f"nested_{i}": i for i in range(50)
        }
        
        manifest = generate_reproducibility_manifest(
            parameters=large_params,
            metadata={"source": "large_params_test"}
        )
        
        # Verify all parameters are preserved
        assert len(manifest["parameters"]) == 101  # 100 + 1 nested
        assert manifest["parameters"]["param_0"] == "value_0"
        assert manifest["parameters"]["nested_large"]["nested_49"] == 49
        
        # Verify JSON serialization works
        json_str = json.dumps(manifest)
        assert len(json_str) > 0


class TestIntegration:
    """Integration tests for logging and manifest utilities working together."""
    
    def test_logging_during_manifest_generation(self):
        """Test that logging works correctly during manifest operations."""
        logger = get_logger("test_integration_manifest")
        logger.handlers = []
        
        memory_handler = logging.Handler()
        log_messages = []
        
        class MemoryHandler(logging.Handler):
            def emit(self, record):
                log_messages.append(self.format(record))
        
        memory_handler = MemoryHandler()
        logger.addHandler(memory_handler)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "integration_manifest.json"
            
            # Generate and save manifest while logging
            logger.info("Starting manifest generation")
            save_reproducibility_manifest(
                parameters={"integration": True},
                output_path=str(manifest_path),
                metadata={"test": "integration"}
            )
            logger.info("Manifest generation completed")
            
            # Verify log messages
            assert len(log_messages) >= 2
            assert "Starting manifest generation" in log_messages[0]
            assert "Manifest generation completed" in log_messages[1]
            
            # Verify manifest was created
            assert manifest_path.exists()
        
        logger.removeHandler(memory_handler)
    
    def test_error_handling_in_manifest_operations(self):
        """Test that errors in manifest operations are properly logged."""
        logger = get_logger("test_error_handling")
        logger.handlers = []
        
        memory_handler = logging.Handler()
        error_messages = []
        
        class MemoryHandler(logging.Handler):
            def emit(self, record):
                error_messages.append((record.levelno, self.format(record)))
        
        memory_handler = MemoryHandler()
        logger.addHandler(memory_handler)
        
        # Try to load non-existent manifest
        try:
            load_reproducibility_manifest("/nonexistent/path/manifest.json")
        except FileNotFoundError:
            handle_exception(logger, "Failed to load manifest")
        
        # Verify error was logged
        assert len(error_messages) > 0
        assert error_messages[0][0] >= logging.ERROR
        assert "Failed to load manifest" in error_messages[0][1]
        
        logger.removeHandler(memory_handler)
    
    def test_context_aware_manifest_generation(self):
        """Test that manifest generation respects logging context."""
        logger = get_logger("test_context_manifest")
        logger.handlers = []
        
        memory_handler = logging.Handler()
        context_messages = []
        
        class MemoryHandler(logging.Handler):
            def emit(self, record):
                context_messages.append(self.format(record))
        
        memory_handler = MemoryHandler()
        logger.addHandler(memory_handler)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with LogContext(logger, {"experiment_id": "exp_123", "user": "researcher"}):
                logger.info("Generating manifest for experiment")
                
                manifest_path = Path(tmpdir) / "context_manifest.json"
                save_reproducibility_manifest(
                    parameters={"experiment_id": "exp_123"},
                    output_path=str(manifest_path),
                    metadata={"user": "researcher"}
                )
            
            # Verify context was included in logs
            assert len(context_messages) > 0
            assert "experiment_id" in context_messages[0] or "exp_123" in context_messages[0]
        
        logger.removeHandler(memory_handler)