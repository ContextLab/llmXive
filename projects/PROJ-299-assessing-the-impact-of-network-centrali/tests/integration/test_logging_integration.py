import json
import logging
import tempfile
from pathlib import Path

import pytest

from code.utils.logging_config import setup_logging, log_event


class TestLoggingIntegration:
    def test_full_pipeline_log_flow(self):
        """
        Simulate a full pipeline flow: setup, log events at different stages,
        and verify the log file contains valid JSON entries for each stage.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "pipeline.log"

            # 1. Setup logging
            logger = setup_logging(log_file=log_file, console_output=False)

            # 2. Simulate pipeline stages
            log_event(logger, "START", "Pipeline started", {"pipeline_id": "T005_test"})
            log_event(logger, "PROCESS", "Downloading data", {"source": "ADNI", "batch": 1})
            log_event(logger, "ERROR", "Connection timeout", {"retry_count": 3}, level=logging.ERROR)
            log_event(logger, "END", "Pipeline finished", {"status": "partial_success"})

            # 3. Verify log file content
            assert log_file.exists()
            assert log_file.stat().st_size > 0

            with open(log_file, "r") as f:
                lines = f.readlines()

            # We expect 4 log entries
            assert len(lines) == 4

            # Parse and validate each entry
            events = []
            for line in lines:
                entry = json.loads(line)
                assert "timestamp" in entry
                assert "level" in entry
                assert "message" in entry
                assert "data" in entry
                events.append(entry["data"]["event_type"])

            # Verify event order
            assert events == ["START", "PROCESS", "ERROR", "END"]

    def test_log_rotation_compatibility(self):
        """
        Test that the log file format is compatible with standard log rotation
        (i.e., each line is a complete JSON object).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "pipeline.log"
            logger = setup_logging(log_file=log_file, console_output=False)

            # Log many entries
            for i in range(100):
                log_event(logger, "TEST", f"Entry {i}", {"index": i})

            # Verify each line is valid JSON
            with open(log_file, "r") as f:
                for line in f:
                    json.loads(line)  # Should not raise
