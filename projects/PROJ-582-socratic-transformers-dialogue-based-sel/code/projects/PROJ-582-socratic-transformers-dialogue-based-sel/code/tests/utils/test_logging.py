"""
Contract tests for the SocraticLogger utility.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.utils.logging import SocraticLogger, get_logger


class TestSocraticLogger:
    """Tests for the SocraticLogger class."""

    def test_log_degenerate_event_creates_jsonl(self, tmp_path: Path):
        """Test that log_degenerate_event creates a valid JSONL file."""
        log_file = tmp_path / "test_events.jsonl"
        logger = SocraticLogger(log_file=log_file)

        logger.log_degenerate_event(
            event_type="critique_failure",
            question="What is 2+2?",
            initial_answer="5",
            error_reason="invalid_arithmetic",
            metadata={"model": "test-model"},
        )

        assert log_file.exists()
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["event_type"] == "critique_failure"
        assert record["data"]["question"] == "What is 2+2?"
        assert record["data"]["error_reason"] == "invalid_arithmetic"
        assert record["data"]["metadata"]["model"] == "test-model"

    def test_log_degenerate_event_appends(self, tmp_path: Path):
        """Test that multiple events are appended correctly."""
        log_file = tmp_path / "test_events.jsonl"
        logger = SocraticLogger(log_file=log_file)

        logger.log_degenerate_event(event_type="event1", metadata={"id": 1})
        logger.log_degenerate_event(event_type="event2", metadata={"id": 2})

        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        assert len(lines) == 2
        record1 = json.loads(lines[0])
        record2 = json.loads(lines[1])
        assert record1["data"]["metadata"]["id"] == 1
        assert record2["data"]["metadata"]["id"] == 2

    def test_log_critique_failure(self, tmp_path: Path):
        """Test the convenience method for critique failures."""
        log_file = tmp_path / "test_events.jsonl"
        logger = SocraticLogger(log_file=log_file)

        logger.log_critique_failure(
            question="Solve for x",
            initial_answer="x=5",
            failure_mode="no_critique_generated",
            details={"token_count": 10},
        )

        with open(log_file, "r", encoding="utf-8") as f:
            record = json.loads(f.readline())
        
        assert record["event_type"] == "critique_failure"
        assert record["data"]["error_reason"] == "no_critique_generated"
        assert record["data"]["metadata"]["token_count"] == 10

    def test_log_revision_failure(self, tmp_path: Path):
        """Test the convenience method for revision failures."""
        log_file = tmp_path / "test_events.jsonl"
        logger = SocraticLogger(log_file=log_file)

        logger.log_revision_failure(
            question="What is the capital of France?",
            initial_answer="Paris",
            critique="That is correct.",
            failure_mode="circular_logic",
        )

        with open(log_file, "r", encoding="utf-8") as f:
            record = json.loads(f.readline())
        
        assert record["event_type"] == "revision_failure"
        assert record["data"]["critique"] == "That is correct."

    def test_log_dialogue_success(self, tmp_path: Path):
        """Test logging a successful dialogue tuple."""
        log_file = tmp_path / "test_events.jsonl"
        logger = SocraticLogger(log_file=log_file)

        logger.log_dialogue_success(
            question="What is 2+2?",
            initial_answer="4",
            critique="Check your arithmetic.",
            revised_answer="4",
            metadata={"timing_ms": 120},
        )

        with open(log_file, "r", encoding="utf-8") as f:
            record = json.loads(f.readline())
        
        assert record["event_type"] == "dialogue_success"
        assert record["data"]["revised_answer"] == "4"
        assert record["data"]["metadata"]["timing_ms"] == 120

    def test_get_logger_factory(self, tmp_path: Path):
        """Test the get_logger factory function."""
        log_file = tmp_path / "factory_test.jsonl"
        logger = get_logger(log_file=log_file)
        
        assert isinstance(logger, SocraticLogger)
        logger.log_degenerate_event(event_type="test", metadata={"factory": True})
        
        assert log_file.exists()
        with open(log_file, "r") as f:
            record = json.loads(f.readline())
        assert record["data"]["metadata"]["factory"] is True

    def test_no_timestamp_option(self, tmp_path: Path):
        """Test logging without timestamps."""
        log_file = tmp_path / "no_ts.jsonl"
        logger = SocraticLogger(log_file=log_file, include_timestamp=False)

        logger.log_degenerate_event(event_type="test")

        with open(log_file, "r") as f:
            record = json.loads(f.readline())
        
        assert record["timestamp"] is None