"""Unit tests for the logging infrastructure (T014)."""

import logging
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from src.utils.logger import (
    get_logger,
    log_data_count,
    log_error,
    log_checksum,
    log_pipeline_stage,
    setup_default_logger,
)


class TestLogger:
    def test_get_logger_returns_logger(self):
        logger = get_logger("test_logger_t014")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_idempotent(self):
        logger1 = get_logger("test_logger_t014_b")
        logger2 = get_logger("test_logger_t014_b")
        assert logger1 is logger2

    def test_log_data_count(self, caplog):
        logger = get_logger("test_logger_t014_c")
        with caplog.at_level(logging.INFO, logger=logger.name):
            log_data_count(logger, "ToxCast", 1234, "loaded")
        assert "DATA_COUNT" in caplog.text
        assert "count=1234" in caplog.text

    def test_log_error(self, caplog):
        logger = get_logger("test_logger_t014_d")
        with caplog.at_level(logging.ERROR, logger=logger.name):
            log_error(logger, "DownloadError", "fetch failed", context={"url": "x"})
        assert "ERROR" in caplog.text
        assert "DownloadError" in caplog.text

    def test_log_checksum(self, caplog):
        logger = get_logger("test_logger_t014_e")
        with caplog.at_level(logging.INFO, logger=logger.name):
            log_checksum(logger, "data/raw/toxcast.csv", "abc123")
        assert "CHECKSUM" in caplog.text
        assert "abc123" in caplog.text

    def test_log_pipeline_stage(self, caplog):
        logger = get_logger("test_logger_t014_f")
        with caplog.at_level(logging.INFO, logger=logger.name):
            log_pipeline_stage(logger, "download", "completed",
                               duration_seconds=1.5, metrics={"rows": 10})
        assert "PIPELINE" in caplog.text
        assert "stage=download" in caplog.text

    def test_setup_default_logger(self):
        logger = setup_default_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "toxicity_pipeline"