import pytest
import logging
import os
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import setup_logging
from generate_data import load_protocol, generate_participant_data
from ingest import run_ingestion, check_sensory_deprivation_tags

class TestLoggingConfig:
    """Tests for logging configuration and output."""

    def test_setup_logging_creates_console_handler(self):
        """Verify that setup_logging creates a console handler."""
        logger = setup_logging(log_level=logging.INFO)
        assert len(logger.handlers) > 0
        has_console = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert has_console

    def test_setup_logging_file_handler(self, tmp_path):
        """Verify that setup_logging can create a file handler."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_level=logging.INFO, log_file=str(log_file))
        assert len(logger.handlers) > 0
        has_file = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert has_file
        assert log_file.exists()

    def test_log_contains_timestamp(self, tmp_path):
        """Verify that log output contains timestamps."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_level=logging.INFO, log_file=str(log_file))
        
        logger.info("Test message")
        
        with open(log_file, 'r') as f:
            content = f.read()
        
        assert "Test message" in content
        assert "|" in content  # Separator in format

class TestGenerateDataLogging:
    """Tests for logging in data generation."""

    def test_load_protocol_logs_info(self, caplog, tmp_path):
        """Verify that load_protocol logs loading info."""
        # Create a mock protocol file
        protocol_file = tmp_path / "protocol.yaml"
        protocol_file.write_text("N: 100\nICC: 0.3\n")
        
        with caplog.at_level(logging.INFO):
            load_protocol(str(protocol_file))
        
        assert "Loading protocol" in caplog.text
        assert "Protocol loaded successfully" in caplog.text

    def test_generate_participant_data_logs_shape(self, caplog):
        """Verify that generate_participant_data logs data shape."""
        protocol = {"N": 10, "effect_sizes": [0.5], "ICC": 0.3}
        
        with caplog.at_level(logging.INFO):
            df = generate_participant_data(protocol, seed=42)
        
        assert "Generating synthetic data" in caplog.text
        assert "Generated data shape" in caplog.text

class TestIngestLogging:
    """Tests for logging in data ingestion."""

    def test_run_ingestion_logs_source(self, caplog, tmp_path):
        """Verify that run_ingestion logs the ingestion source."""
        # Create a minimal protocol file
        protocol_file = tmp_path / "protocol.yaml"
        protocol_file.write_text("""
        N: 200
        ICC: 0.3
        effect_sizes: [0.5, 0.0, -0.2]
        strict_threshold_label: "strict (complete isolation)"
        moderate_threshold_label: "moderate (partial sensory reduction)"
        partial_threshold_label: "partial (minimal sensory reduction)"
        """)
        
        with caplog.at_level(logging.INFO):
            # Run ingestion without input path (will generate synthetic)
            with patch('ingest.load_protocol', return_value={
                "N": 200,
                "ICC": 0.3,
                "effect_sizes": [0.5, 0.0, -0.2],
                "strict_threshold_label": "strict",
                "moderate_threshold_label": "moderate",
                "partial_threshold_label": "partial"
            }):
                with patch('ingest.generate_synthetic_datasets', return_value=["fake.csv"]):
                    with patch('ingest.ingest_csv', return_value=pd.DataFrame({
                        'condition': ['strict'],
                        'recall': [1],
                        'bizarreness': [5],
                        'participant_id': [1],
                        'is_synthetic': [True],
                        'ingestion_source': ['synthetic_auto']
                    })):
                        run_ingestion(protocol_path=str(protocol_file))
        
        assert "Starting Data Ingestion Pipeline" in caplog.text
        assert "Ingestion source" in caplog.text

    def test_check_sensory_deprivation_tags_logs_result(self, caplog):
        """Verify that check_sensory_deprivation_tags logs the result."""
        import pandas as pd
        df = pd.DataFrame({'condition': ['sensory_deprivation_test']})
        
        with caplog.at_level(logging.INFO):
            result = check_sensory_deprivation_tags(df)
        
        assert "Found sensory deprivation tags" in caplog.text
        assert result is True

class TestRealVsSyntheticLogging:
    """Tests specifically for distinguishing real vs synthetic data logging."""

    def test_synthetic_data_logs_parameters(self, caplog):
        """Verify that synthetic data generation logs all key parameters."""
        protocol = {
            "N": 200,
            "ICC": 0.3,
            "effect_sizes": [0.5, 0.0, -0.2],
            "strict_threshold_label": "strict",
            "moderate_threshold_label": "moderate",
            "partial_threshold_label": "partial"
        }
        
        with caplog.at_level(logging.INFO):
            # Mock the generation to avoid actual file writing
            with patch('generate_data.np.random.binomial', return_value=[1]*10):
                with patch('generate_data.np.random.normal', return_value=[0]*10):
                    with patch('generate_data.np.random.randint', return_value=[5]*10):
                        generate_participant_data(protocol, seed=42)
        
        assert "N=200" in caplog.text or "Sample Size" in caplog.text
        assert "Effect Sizes" in caplog.text or "effect_sizes" in caplog.text

    def test_ingestion_logs_source_type(self, caplog):
        """Verify that ingestion logs whether data is real or synthetic."""
        with caplog.at_level(logging.INFO):
            # Simulate synthetic ingestion
            with patch('ingest.load_protocol', return_value={"N": 100, "ICC": 0.3, "effect_sizes": [0.5]}):
                with patch('ingest.auto_generate_data') as mock_gen:
                    mock_gen.return_value = pd.DataFrame({
                        'condition': ['strict'],
                        'recall': [1],
                        'bizarreness': [5],
                        'participant_id': [1],
                        'ingestion_source': ['synthetic_auto']
                    })
                    run_ingestion()
        
        assert "synthetic_auto" in caplog.text or "synthetic" in caplog.text

    def test_real_data_logs_source(self, caplog):
        """Verify that real data ingestion logs the source correctly."""
        import pandas as pd
        with caplog.at_level(logging.INFO):
            with patch('ingest.ingest_csv', return_value=pd.DataFrame({
                'condition': ['strict'],
                'recall': [1],
                'bizarreness': [5],
                'participant_id': [1],
                'is_synthetic': [False],
                'ingestion_source': ['real_csv']
            })):
                with patch('ingest.check_sensory_deprivation_tags', return_value=True):
                    run_ingestion(input_path="fake.csv")
        
        assert "real_csv" in caplog.text or "real data" in caplog.text