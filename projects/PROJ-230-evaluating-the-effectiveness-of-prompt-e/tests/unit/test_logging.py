import json
import logging
import os
import tempfile
from pathlib import Path
import pytest
from datetime import datetime

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.utils.logging import (
    get_logger,
    JsonFormatter,
    log_prompt,
    log_raw_output,
    log_evaluation_result,
    LOG_DIR
)

@pytest.fixture
def temp_log_dir(monkeypatch):
    """Create a temporary directory for logs during tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        # Monkeypatch the LOG_DIR constant
        monkeypatch.setattr("src.utils.logging.LOG_DIR", temp_path)
        # Also need to ensure the module sees the new path if it was imported
        # Re-importing might be tricky, so we rely on the fixture setting the attribute
        # before the functions use it.
        yield temp_path

def test_json_formatter_format():
    """Test that JsonFormatter produces valid JSON."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None
    )
    # Add extra data
    record.extra_data = {"key": "value"}

    output = formatter.format(record)
    data = json.loads(output)

    assert "timestamp" in data
    assert data["level"] == "INFO"
    assert data["message"] == "Test message"
    assert data["key"] == "value"

def test_get_logger_creates_handlers(temp_log_dir):
    """Test that get_logger creates console and file handlers."""
    logger = get_logger("test_logger_1", log_file="test_1.jsonl")

    # Should have at least 2 handlers (console + file)
    assert len(logger.handlers) >= 2

    # Check file handler exists
    file_handler = next((h for h in logger.handlers if isinstance(h, logging.FileHandler)), None)
    assert file_handler is not None
    assert file_handler.baseFilename == str(temp_log_dir / "test_1.jsonl")

def test_log_prompt(temp_log_dir):
    """Test that log_prompt writes correct JSON to log."""
    logger = get_logger("test_logger_2", log_file="test_2.jsonl")
    log_prompt(
        logger=logger,
        prompt_id="p-1",
        condition="zero_shot",
        seed=123,
        prompt_text="Hello",
        model_version="v1"
    )

    log_file = temp_log_dir / "test_2.jsonl"
    assert log_file.exists()

    with open(log_file, 'r') as f:
        line = f.readline()
        data = json.loads(line)

    assert data["event_type"] == "prompt"
    assert data["prompt_id"] == "p-1"
    assert data["condition"] == "zero_shot"
    assert data["seed"] == 123
    assert data["model_version"] == "v1"

def test_log_raw_output_success(temp_log_dir):
    """Test logging a successful raw output."""
    logger = get_logger("test_logger_3", log_file="test_3.jsonl")
    log_raw_output(
        logger=logger,
        prompt_id="p-2",
        raw_output="result",
        status="success",
        latency_ms=50.0
    )

    log_file = temp_log_dir / "test_3.jsonl"
    with open(log_file, 'r') as f:
        data = json.loads(f.readline())

    assert data["event_type"] == "raw_output"
    assert data["status"] == "success"
    assert data["latency_ms"] == 50.0
    assert data["output_length"] == 6

def test_log_raw_output_error(temp_log_dir):
    """Test logging a failed raw output."""
    logger = get_logger("test_logger_4", log_file="test_4.jsonl")
    log_raw_output(
        logger=logger,
        prompt_id="p-3",
        raw_output="",
        status="failed",
        error_message="Timeout"
    )

    log_file = temp_log_dir / "test_4.jsonl"
    with open(log_file, 'r') as f:
        data = json.loads(f.readline())

    assert data["status"] == "failed"
    assert data["error"] == "Timeout"

def test_log_evaluation_result(temp_log_dir):
    """Test logging an evaluation result."""
    logger = get_logger("test_logger_5", log_file="test_5.jsonl")
    log_evaluation_result(
        logger=logger,
        translation_id="t-1",
        prompt_id="p-4",
        is_correct=True,
        complexity_score=2.5,
        loc=10,
        condition="few_shot"
    )

    log_file = temp_log_dir / "test_5.jsonl"
    with open(log_file, 'r') as f:
        data = json.loads(f.readline())

    assert data["event_type"] == "evaluation"
    assert data["is_correct"] is True
    assert data["complexity_score"] == 2.5
    assert data["loc"] == 10
    assert data["condition"] == "few_shot"