import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
import logging

from src.logging_config import setup_logging
from src.data_loader import log_skipped_record, calculate_gain_scores, load_public_dataset
from src.synthetic_gen import SyntheticDataGenerator, generate_mapping_log
from src.models import DatasetRecord

class TestLoggingIntegration:
    @pytest.fixture
    def temp_dir(self):
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    def test_setup_logging_creates_file(self, temp_dir):
        log_file = Path(temp_dir) / "test.log"
        logger = setup_logging(log_file=str(log_file))
        
        logger.info("Test message")
        
        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
            assert "Test message" in content

    def test_log_skipped_record_writes_jsonl(self, temp_dir):
        log_file = Path(temp_dir) / "skipped.log"
        record = {"index": 1, "pre": 10, "post": None}
        
        log_skipped_record(record, "Missing post score", log_file)
        
        assert log_file.exists()
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["reason"] == "Missing post score"
            assert data["skipped_data"]["index"] == 1

    def test_synthetic_gen_logs_parameters(self, temp_dir, caplog):
        # Set up logging to capture to caplog
        caplog.set_level(logging.INFO)
        
        generator = SyntheticDataGenerator(seed=42, n_samples=100)
        generator.generate()
        
        assert any("Generated 100 synthetic records" in message for message in caplog.messages)
        assert any("SyntheticDataGenerator initialized" in message for message in caplog.messages)

    def test_mapping_log_creation(self, temp_dir):
        output_path = Path(temp_dir) / "mapping_log.json"
        generate_mapping_log(str(output_path), {"test": "param"})
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
            assert "concepts" in data
            assert data["concepts"][0]["physics_concept"] is not None