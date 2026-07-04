import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
import logging

from src.logging_config import setup_logging
from src.data_loader import load_public_dataset, calculate_gain_scores, log_skipped_record
from src.synthetic_gen import SyntheticDataGenerator
from src.models import DatasetRecord

class TestLoggingIntegration:
    """Tests to verify logging is correctly implemented for T017."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory structure for testing."""
        temp_dir = tempfile.mkdtemp()
        # Create required subdirectories
        (Path(temp_dir) / "data" / "derivation_logs").mkdir(parents=True)
        (Path(temp_dir) / "data" / "synthetic").mkdir(parents=True)
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_setup_logging_creates_handlers(self, temp_project_root):
        """Test that setup_logging creates both console and file handlers."""
        log_file = "data/derivation_logs/test.log"
        logger = setup_logging(log_file=log_file, project_root=Path(temp_project_root))
        
        assert len(logger.handlers) >= 2  # Console + File
        assert logger.level == logging.INFO

    def test_data_loader_logs_load(self, temp_project_root):
        """Test that load_public_dataset logs the loading process."""
        # Create a dummy CSV
        csv_path = Path(temp_project_root) / "data" / "test.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, 'w') as f:
            f.write("pre_test_score,post_test_score,instruction_type\n")
            f.write("50,60,embodied\n")
            f.write("50,55,static\n")
        
        logger = logging.getLogger("embodied_curriculum")
        # Capture log output? For now, just ensure it runs without error and logs to file
        records = load_public_dataset(str(csv_path), project_root=Path(temp_project_root))
        
        assert len(records) == 2
        # Check if log file exists
        log_path = Path(temp_project_root) / "data" / "derivation_logs" / "process.log"
        assert log_path.exists()

    def test_synthetic_gen_logs_generation(self, temp_project_root):
        """Test that SyntheticDataGenerator logs parameters."""
        gen = SyntheticDataGenerator(seed=42)
        records = gen.generate(n_samples=10)
        
        assert len(records) == 10
        # Check log file
        log_path = Path(temp_project_root) / "data" / "derivation_logs" / "synthetic.log"
        assert log_path.exists()

    def test_generate_mapping_log_creates_file(self, temp_project_root):
        """Test that generate_mapping_log creates the required JSON file."""
        gen = SyntheticDataGenerator(seed=42)
        output_path = str(Path(temp_project_root) / "data" / "synthetic" / "mapping_log.json")
        
        result_path = gen.generate_mapping_log(output_path)
        
        assert os.path.exists(result_path)
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        assert "causal_chain" in data
        assert len(data["causal_chain"]) == 3
        assert data["causal_chain"][0]["stage"] == "Physics_Action"

    def test_calculate_gain_scores_logs_skipped(self, temp_project_root):
        """Test that calculate_gain_scores logs skipped records."""
        # Create records with one missing score
        records = [
            DatasetRecord(pre_test_score=50.0, post_test_score=60.0, instruction_type="test", covariates={}),
            DatasetRecord(pre_test_score=None, post_test_score=60.0, instruction_type="test", covariates={}),
        ]
        
        processed = calculate_gain_scores(records)
        
        assert len(processed) == 1
        # Check log file
        log_path = Path(temp_project_root) / "data" / "derivation_logs" / "skipped_records.log"
        assert log_path.exists()