import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
import logging
import sys

from src.logging_config import setup_logging
from src.data_loader import log_skipped_record, calculate_gain_scores
from src.models import DatasetRecord
from src.synthetic_gen import SyntheticDataGenerator, generate_mapping_log

class TestLogging:
    def test_setup_logging_console(self, caplog):
        """Test that logging setup works for console output."""
        logger = setup_logging(log_level=logging.INFO)
        assert logger.level == logging.INFO
        
        with caplog.at_level(logging.INFO):
            logger.info("Test message")
        assert "Test message" in caplog.text

    def test_setup_logging_file(self, tmp_path):
        """Test that logging setup works for file output."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_level=logging.DEBUG, log_file=str(log_file))
        
        logger.debug("Debug message")
        logger.info("Info message")
        
        assert log_file.exists()
        content = log_file.read_text()
        assert "Debug message" in content
        assert "Info message" in content

    def test_log_skipped_record(self, tmp_path, caplog):
        """Test that skipped records are logged correctly."""
        # Mock the log file path
        log_dir = tmp_path / "data" / "derivation_logs"
        log_dir.mkdir(parents=True)
        log_file = log_dir / "skipped_records.log"
        
        # Temporarily override the log path in the function
        # Since the function uses a hardcoded path, we can't easily mock it without refactoring
        # Instead, we test the logging output
        with caplog.at_level(logging.WARNING):
            log_skipped_record(record_id="123", reason="Missing score", source="test.csv")
        assert "Skipped record 123" in caplog.text
        assert "Missing score" in caplog.text

    def test_calculate_gain_scores_logging(self, caplog):
        """Test that gain score calculation logs correctly."""
        records = [
            DatasetRecord(pre_test_score=50.0, post_test_score=60.0, instruction_type="embodied", covariates={}),
            DatasetRecord(pre_test_score=50.0, post_test_score=None, instruction_type="static", covariates={}) # Missing post
        ]
        
        with caplog.at_level(logging.WARNING):
            processed = calculate_gain_scores(records)
        
        # Should log a warning for the missing record
        assert "Skipped record" in caplog.text
        # Should process the valid record
        assert len(processed) == 1
        assert hasattr(processed[0], 'gain_score')
        assert processed[0].gain_score == 10.0

    def test_synthetic_generation_logging(self, caplog):
        """Test that synthetic data generation logs parameters."""
        with caplog.at_level(logging.INFO):
            generator = SyntheticDataGenerator(seed=42)
            records = generator.generate(n_samples=100)
        
        assert "SyntheticDataGenerator initialized with seed 42" in caplog.text
        assert "Generating 100 synthetic records." in caplog.text
        assert "Generated 100 synthetic records." in caplog.text

    def test_mapping_log_generation(self, tmp_path, caplog):
        """Test that mapping log is generated and logged."""
        output_path = str(tmp_path / "mapping_log.json")
        
        with caplog.at_level(logging.INFO):
            generate_mapping_log(output_path)
        
        assert "Generating mapping log" in caplog.text
        assert "Mapping log generated successfully" in caplog.text
        
        # Verify file exists and has content
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert "physics_param" in data
        assert "math_concept" in data
        assert "mapping_rule" in data