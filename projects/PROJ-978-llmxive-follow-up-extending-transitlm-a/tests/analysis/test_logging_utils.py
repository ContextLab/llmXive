"""
Tests for logging utilities in analysis/logging_utils.py
"""
import json
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from analysis.logging_utils import (
    setup_logger,
    log_prediction,
    log_validity_score,
    log_risk_flag,
    log_chi_squared_result,
    log_evaluation_summary,
    log_topological_metrics,
    init_evaluation_logging
)


class TestSetupLogger:
    def test_setup_logger_console_only(self):
        """Test logger setup with console output only."""
        logger = setup_logger("test_console", console=True, log_file=None)
        assert logger is not None
        assert len(logger.handlers) >= 1

    def test_setup_logger_file_only(self):
        """Test logger setup with file output only."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            logger = setup_logger("test_file", log_file=tmp_path, console=False)
            assert logger is not None
            assert len(logger.handlers) >= 1

            # Test logging
            logger.info("Test message")

            # Verify file has content
            with open(tmp_path, "r") as f:
                content = f.read()
            assert "Test message" in content
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_setup_logger_both(self):
        """Test logger setup with both console and file output."""
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            logger = setup_logger("test_both", log_file=tmp_path, console=True)
            assert len(logger.handlers) >= 2
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


class TestLogPrediction:
    def test_log_valid_prediction(self, caplog):
        """Test logging a valid prediction."""
        logger = setup_logger("test_valid", console=True, log_file=None)

        with caplog.at_level(logging.INFO):
            log_prediction(
                logger=logger,
                route_id="route_1",
                model_name="test_model",
                predicted_stations=["A", "B", "C"],
                ground_truth_stations=["A", "B", "C"],
                is_valid=True,
                confidence=0.95
            )

        assert "PREDICTION_VALID" in caplog.text
        assert "route_1" in caplog.text

    def test_log_invalid_prediction(self, caplog):
        """Test logging an invalid prediction."""
        logger = setup_logger("test_invalid", console=True, log_file=None)

        with caplog.at_level(logging.WARNING):
            log_prediction(
                logger=logger,
                route_id="route_2",
                model_name="test_model",
                predicted_stations=["A", "B", "X"],
                ground_truth_stations=["A", "B", "C"],
                is_valid=False,
                confidence=0.5
            )

        assert "PREDICTION_INVALID" in caplog.text


class TestLogValidityScore:
    def test_log_validity_score(self, caplog):
        """Test logging validity score."""
        logger = setup_logger("test_validity", console=True, log_file=None)

        with caplog.at_level(logging.INFO):
            log_validity_score(
                logger=logger,
                model_name="test_model",
                category="short",
                route_count=100,
                valid_count=85,
                validity_rate=0.85
            )

        assert "VALIDITY_SCORE" in caplog.text
        assert "short" in caplog.text
        assert "0.85" in caplog.text


class TestLogRiskFlag:
    def test_log_high_risk(self, caplog):
        """Test logging high risk flag."""
        logger = setup_logger("test_risk_high", console=True, log_file=None)

        with caplog.at_level(logging.ERROR):
            log_risk_flag(
                logger=logger,
                route_id="route_3",
                model_name="test_model",
                risk_level="HIGH",
                reason="Exceeds cognitive horizon",
                metrics={"route_length": 50}
            )

        assert "HIGH_RISK_FLAG" in caplog.text
        assert "Exceeds cognitive horizon" in caplog.text

    def test_log_medium_risk(self, caplog):
        """Test logging medium risk flag."""
        logger = setup_logger("test_risk_med", console=True, log_file=None)

        with caplog.at_level(logging.WARNING):
            log_risk_flag(
                logger=logger,
                route_id="route_4",
                model_name="test_model",
                risk_level="MEDIUM",
                reason="Near cognitive horizon",
                metrics={"route_length": 30}
            )

        assert "MEDIUM_RISK_FLAG" in caplog.text

    def test_log_low_risk(self, caplog):
        """Test logging low risk flag."""
        logger = setup_logger("test_risk_low", console=True, log_file=None)

        with caplog.at_level(logging.INFO):
            log_risk_flag(
                logger=logger,
                route_id="route_5",
                model_name="test_model",
                risk_level="LOW",
                reason="Normal operation",
                metrics={"route_length": 10}
            )

        assert "LOW_RISK_FLAG" in caplog.text


class TestLogChiSquaredResult:
    def test_log_significant_degradation(self, caplog):
        """Test logging significant degradation."""
        logger = setup_logger("test_chi_sig", console=True, log_file=None)

        with caplog.at_level(logging.WARNING):
            log_chi_squared_result(
                logger=logger,
                route_length=25,
                chi_squared_stat=15.5,
                p_value=0.001,
                is_significant=True,
                validity_gap=20.0
            )

        assert "SIGNIFICANT_DEGRADATION" in caplog.text

    def test_log_non_significant(self, caplog):
        """Test logging non-significant result."""
        logger = setup_logger("test_chi_nonsig", console=True, log_file=None)

        with caplog.at_level(logging.INFO):
            log_chi_squared_result(
                logger=logger,
                route_length=20,
                chi_squared_stat=2.5,
                p_value=0.15,
                is_significant=False,
                validity_gap=5.0
            )

        assert "CHI_SQUARED_RESULT" in caplog.text


class TestLogEvaluationSummary:
    def test_log_evaluation_summary(self, caplog):
        """Test logging evaluation summary."""
        logger = setup_logger("test_summary", console=True, log_file=None)

        categories = {
            "short": {"total": 50, "valid": 45, "validity_rate": 0.9},
            "medium": {"total": 30, "valid": 20, "validity_rate": 0.67},
            "long": {"total": 20, "valid": 5, "validity_rate": 0.25}
        }

        with caplog.at_level(logging.INFO):
            log_evaluation_summary(
                logger=logger,
                model_name="test_model",
                total_routes=100,
                overall_validity=0.7,
                categories=categories,
                inflection_point=25,
                high_risk_count=10
            )

        assert "EVALUATION_SUMMARY" in caplog.text
        assert "inflection_point_route_length" in caplog.text
        assert "25" in caplog.text


class TestLogTopologicalMetrics:
    def test_log_topological_metrics(self, caplog):
        """Test logging topological metrics."""
        logger = setup_logger("test_topo", console=True, log_file=None)

        with caplog.at_level(logging.DEBUG):
            log_topological_metrics(
                logger=logger,
                route_id="route_6",
                betweenness_centrality=0.45,
                path_complexity=12.5,
                category="medium"
            )

        assert "TOPOLOGICAL_METRICS" in caplog.text
        assert "route_6" in caplog.text


class TestInitEvaluationLogging:
    def test_init_evaluation_logging_creates_file(self):
        """Test that init_evaluation_logging creates a log file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "test_eval.log"

            logger = init_evaluation_logging(
                log_dir=tmp_dir,
                log_filename="test_eval.log"
            )

            logger.info("Test initialization message")

            assert log_path.exists()
            with open(log_path, "r") as f:
                content = f.read()
            assert "Test initialization message" in content