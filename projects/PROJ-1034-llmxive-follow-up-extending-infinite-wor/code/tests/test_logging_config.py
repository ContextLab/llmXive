import pytest
import json
import os
import tempfile
from datetime import datetime
from io import StringIO
import csv

from sim.logging_config import MetricRecord, SimulationLogger, create_logger

class TestSimulationLogger:
    def test_logger_initialization(self):
        """Test that logger creates necessary directories and files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SimulationLogger(output_dir=tmpdir, filename_prefix="test")
            assert os.path.exists(logger.csv_path)
            assert not os.path.exists(logger.json_path)  # JSON only written on finish
            assert logger.metrics == []
            assert logger.step_count == 0

    def test_log_step_records_metrics(self):
        """Test that log_step correctly records coherence, diversity, and latency."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SimulationLogger(output_dir=tmpdir, filename_prefix="test")
            logger.start(config_hash="abc123")

            logger.log_step(
                step=0,
                coherence_score=0.85,
                diversity_score=0.42,
                step_latency=0.005,
                config_hash="abc123"
            )

            assert len(logger.metrics) == 1
            record = logger.metrics[0]
            assert record.step == 0
            assert record.coherence_score == 0.85
            assert record.diversity_score == 0.42
            assert record.step_latency == 0.005
            assert record.status == "running"

    def test_log_step_multiple_entries(self):
        """Test logging multiple steps accumulates records."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SimulationLogger(output_dir=tmpdir, filename_prefix="test")
            logger.start()

            for i in range(5):
                logger.log_step(
                    step=i,
                    coherence_score=0.5 + (i * 0.1),
                    diversity_score=0.3 + (i * 0.05),
                    step_latency=0.01 + (i * 0.001)
                )

            assert len(logger.metrics) == 5
            assert logger.step_count == 5

    def test_finish_writes_json(self):
        """Test that finish writes the JSON report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SimulationLogger(output_dir=tmpdir, filename_prefix="test")
            logger.start()
            logger.log_step(0, 0.9, 0.5, 0.01)
            result = logger.finish()

            assert os.path.exists(result["json_path"])
            assert os.path.exists(result["csv_path"])

            with open(result["json_path"], 'r') as f:
                data = json.load(f)
                assert len(data) == 1
                assert data[0]["coherence_score"] == 0.9

    def test_finish_returns_summary(self):
        """Test that finish returns correct duration and path info."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SimulationLogger(output_dir=tmpdir, filename_prefix="test")
            logger.start()
            import time
            time.sleep(0.01)
            logger.log_step(0, 0.9, 0.5, 0.01)
            result = logger.finish()

            assert result["total_steps"] == 1
            assert result["json_path"].endswith(".json")
            assert result["csv_path"].endswith(".csv")
            assert result["total_duration"] >= 0.01

    def test_csv_contains_all_required_fields(self):
        """Verify CSV output contains coherence_score, diversity_score, step_latency."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SimulationLogger(output_dir=tmpdir, filename_prefix="test")
            logger.start()
            logger.log_step(10, 0.75, 0.33, 0.025)
            logger.finish()

            with open(logger.csv_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)

                # Check header
                header = rows[0]
                assert "coherence_score" in header
                assert "diversity_score" in header
                assert "step_latency" in header

                # Check data row
                data_row = rows[1]
                assert float(data_row[2]) == 0.75  # coherence
                assert float(data_row[3]) == 0.33  # diversity
                assert float(data_row[4]) == 0.025 # latency

    def test_get_summary_calculates_averages(self):
        """Test that get_summary correctly computes averages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SimulationLogger(output_dir=tmpdir, filename_prefix="test")
            logger.start()
            logger.log_step(0, 0.8, 0.4, 0.01)
            logger.log_step(1, 0.9, 0.6, 0.02)
            logger.log_step(2, 0.7, 0.2, 0.03)

            summary = logger.get_summary()

            assert summary["total_steps"] == 3
            assert abs(summary["avg_coherence"] - 0.8) < 0.001
            assert abs(summary["avg_diversity"] - 0.4) < 0.001
            assert abs(summary["avg_step_latency"] - 0.02) < 0.001

class TestLoggingIntegration:
    def test_create_logger_factory(self):
        """Test the factory function creates a valid logger."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = create_logger(output_dir=tmpdir, filename_prefix="factory_test")
            assert isinstance(logger, SimulationLogger)
            assert logger.output_dir == tmpdir

    def test_log_status_transitions(self):
        """Test that status transitions are recorded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SimulationLogger(output_dir=tmpdir, filename_prefix="test")
            logger.start()
            logger.log_step(0, 0.5, 0.5, 0.01)
            logger.finish()

            with open(logger.csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                # First row should be running
                assert rows[0]["status"] == "running"
                # Last row should be completed
                assert rows[-1]["status"] == "completed"

    def test_extra_metadata_serialization(self):
        """Test that extra metadata is correctly serialized in CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = SimulationLogger(output_dir=tmpdir, filename_prefix="test")
            logger.start()
            meta = {"param_a": 10, "param_b": "test"}
            logger.log_step(0, 0.5, 0.5, 0.01, extra_metadata=meta)
            logger.finish()

            with open(logger.csv_path, 'r') as f:
                reader = csv.DictReader(f)
                row = next(reader)
                assert "10" in row["extra_metadata"]
                assert "test" in row["extra_metadata"]
