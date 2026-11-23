"""
Unit tests for logging infrastructure.

Tests deterministic logging format, JSON log handler, and mapping log functionality.
"""
import json
import logging
import os
import tempfile
from pathlib import Path
import pytest
from datetime import datetime

from code.logging_config import JSONLogHandler, setup_logging, log_mapping, get_project_logger


class TestJSONLogHandler:
    """Tests for the JSONLogHandler class."""
    
    def test_creates_log_file(self, tmp_path):
        """Test that JSONLogHandler creates the log file."""
        log_path = tmp_path / "test_log.json"
        handler = JSONLogHandler(log_path)
        
        # Trigger a log record
        logger = logging.getLogger("test_json_handler")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.info("Test message")
        
        assert log_path.exists()
    
    def test_writes_valid_json(self, tmp_path):
        """Test that each line in the log file is valid JSON."""
        log_path = tmp_path / "test_log.json"
        handler = JSONLogHandler(log_path)
        
        logger = logging.getLogger("test_json_handler_valid")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.info("Test message")
        
        with open(log_path, 'r') as f:
            line = f.readline()
            # Should be valid JSON
            entry = json.loads(line)
            assert isinstance(entry, dict)
    
    def test_includes_required_fields(self, tmp_path):
        """Test that log entries include all required fields."""
        log_path = tmp_path / "test_log.json"
        handler = JSONLogHandler(log_path)
        
        logger = logging.getLogger("test_json_handler_fields")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.info("Test message")
        
        with open(log_path, 'r') as f:
            entry = json.loads(f.readline())
        
        required_fields = ['timestamp', 'level', 'logger', 'message', 'filename', 'lineno']
        for field in required_fields:
            assert field in entry, f"Missing required field: {field}"
    
    def test_thread_safe(self, tmp_path):
        """Test that JSONLogHandler is thread-safe."""
        import threading
        log_path = tmp_path / "test_log.json"
        handler = JSONLogHandler(log_path)
        
        logger = logging.getLogger("test_json_handler_thread")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        def log_message(msg):
            logger.info(msg)
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=log_message, args=(f"Message {i}",))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        with open(log_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 10
        for line in lines:
            json.loads(line)  # Should not raise


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_returns_logger(self, tmp_path):
        """Test that setup_logging returns a logger."""
        logger = setup_logging(project_root=tmp_path)
        assert isinstance(logger, logging.Logger)
    
    def test_creates_json_log_file(self, tmp_path):
        """Test that setup_logging creates the JSON log file."""
        json_log_path = tmp_path / "data" / "processed" / "mapping_log.json"
        logger = setup_logging(project_root=tmp_path, json_log_path=json_log_path)
        
        # Trigger a log
        logger.info("Test")
        
        assert json_log_path.exists()
    
    def test_console_handler_added(self, tmp_path, capsys):
        """Test that console handler is added when console_output=True."""
        logger = setup_logging(project_root=tmp_path, console_output=True)
        logger.info("Console test")
        
        captured = capsys.readouterr()
        assert "Console test" in captured.out


class TestLogMapping:
    """Tests for log_mapping function."""
    
    def test_logs_mapping_data(self, tmp_path):
        """Test that log_mapping writes correct data to JSON log."""
        json_log_path = tmp_path / "data" / "processed" / "mapping_log.json"
        setup_logging(project_root=tmp_path, json_log_path=json_log_path)
        logger = get_project_logger("test_mapping")
        
        log_mapping(
            logger=logger,
            dataset_id="DS001",
            raw_condition="ignored",
            binary_condition=1,
            source="keyword_match",
            confidence=0.95
        )
        
        with open(json_log_path, 'r') as f:
            entry = json.loads(f.readline())
        
        assert entry['dataset_id'] == "DS001"
        assert entry['raw_condition'] == "ignored"
        assert entry['binary_condition'] == 1
        assert entry['mapping_source'] == "keyword_match"
        assert entry['confidence'] == 0.95
    
    def test_multiple_mappings(self, tmp_path):
        """Test that multiple mappings are logged correctly."""
        json_log_path = tmp_path / "data" / "processed" / "mapping_log.json"
        setup_logging(project_root=tmp_path, json_log_path=json_log_path)
        logger = get_project_logger("test_mapping_multi")
        
        mappings = [
            ("DS001", "excluded", 1, "manual"),
            ("DS002", "control", 0, "keyword_match"),
            ("DS003", "ostracized", 1, "manual"),
        ]
        
        for dataset_id, raw, binary, source in mappings:
            log_mapping(logger, dataset_id, raw, binary, source)
        
        with open(json_log_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        
        for i, line in enumerate(lines):
            entry = json.loads(line)
            expected = mappings[i]
            assert entry['dataset_id'] == expected[0]
            assert entry['raw_condition'] == expected[1]
            assert entry['binary_condition'] == expected[2]