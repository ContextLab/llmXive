import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.utils.logging_config import (
    setup_logging,
    JsonFormatter,
    log_reproducibility_manifest,
    log_evaluation_result,
    log_model_checkpoint,
    log_dataset_subset,
)
from src.models.entities import EvaluationResult, ModelCheckpoint, DatasetSubset


class TestJsonFormatter:
    def test_format_basic_log(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.created = 1609459200.0  # 2021-01-01 00:00:00 UTC

        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["module"] == "test"
        assert "timestamp" in data

    def test_format_with_extra_data(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="Extra data test",
            args=(),
            exc_info=None,
        )
        record.created = 1609459200.0
        record.extra_data = {"key": "value", "number": 42}

        output = formatter.format(record)
        data = json.loads(output)

        assert data["data"]["key"] == "value"
        assert data["data"]["number"] == 42

    def test_format_with_exception(self):
        formatter = JsonFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )
            record.created = 1609459200.0

            output = formatter.format(record)
            data = json.loads(output)

            assert "exception" in data
            assert "ValueError" in data["exception"]


class TestSetupLogging:
    def test_console_only(self, caplog):
        logger = setup_logging(log_file=None, console_output=True, level=logging.INFO)

        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

        logger.info("Test console message")
        assert "Test console message" in caplog.text

    def test_file_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=log_file, console_output=False, level=logging.INFO)

            logger.info("Test file message")

            # Force flush
            for handler in logger.handlers:
                handler.flush()

            assert os.path.exists(log_file)
            with open(log_file, "r") as f:
                content = f.read()
                data = json.loads(content)
                assert data["message"] == "Test file message"

    def test_both_console_and_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=log_file, console_output=True, level=logging.INFO)

            assert len(logger.handlers) == 2


class TestLogReproducibilityManifest:
    def test_manifest_written_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=log_file, console_output=False)

            manifest_data = {
                "seeds": [1, 2, 3, 4, 5],
                "versions": {"torch": "2.3.0", "transformers": "4.40.0"},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            output_path = os.path.join(tmpdir, "manifest.json")

            log_reproducibility_manifest(logger, manifest_data, output_path)

            assert os.path.exists(output_path)
            with open(output_path, "r") as f:
                saved_data = json.load(f)
                assert saved_data["seeds"] == [1, 2, 3, 4, 5]
                assert saved_data["versions"]["torch"] == "2.3.0"


class TestLogEvaluationResult:
    def test_evaluation_logged_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=log_file, console_output=False)

            result = EvaluationResult(
                dataset_subset="test_subset",
                model_checkpoint="checkpoint_epoch_1.pt",
                success_rate=0.85,
                trajectory_length=100,
                variance=0.02,
                ci_95_lower=0.80,
                ci_95_upper=0.90,
            )

            log_evaluation_result(logger, result)

            for handler in logger.handlers:
                handler.flush()

            with open(log_file, "r") as f:
                content = f.read()
                data = json.loads(content)
                assert data["data"]["success_rate"] == 0.85
                assert data["data"]["trajectory_length"] == 100


class TestLogModelCheckpoint:
    def test_checkpoint_logged_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=log_file, console_output=False)

            checkpoint = ModelCheckpoint(
                path=os.path.join(tmpdir, "model.pt"),
                epoch=5,
                size_bytes=1024 * 1024 * 50,
                checksum="abc123",
                timestamp=datetime.now(timezone.utc),
            )

            log_model_checkpoint(logger, checkpoint)

            for handler in logger.handlers:
                handler.flush()

            with open(log_file, "r") as f:
                content = f.read()
                data = json.loads(content)
                assert data["data"]["epoch"] == 5
                assert data["data"]["size_bytes"] == 1024 * 1024 * 50


class TestLogDatasetSubset:
    def test_subset_logged_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(log_file=log_file, console_output=False)

            subset = DatasetSubset(
                name="open_x_filtered",
                source="huggingface/open-x-embodiment",
                num_samples=50000,
                platforms=["franka", "ur5", "kuka"],
                checksum="def456",
            )

            log_dataset_subset(logger, subset)

            for handler in logger.handlers:
                handler.flush()

            with open(log_file, "r") as f:
                content = f.read()
                data = json.loads(content)
                assert data["data"]["num_samples"] == 50000
                assert "franka" in data["data"]["platforms"]