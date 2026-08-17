"""
Integration tests for T015a: generate_dataset_stream.py

Tests verify the streaming loop logic, data loading, and output file creation.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
import pandas as pd
import json

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.cli.generate_dataset_stream import main, load_dataset_streaming, process_single_sample
from src.config.env_config import load_config

class TestGenerateDatasetStream:
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @patch('src.cli.generate_dataset_stream.load_dataset_streaming')
    @patch('src.cli.generate_dataset_stream.extract_features_for_sample')
    @patch('src.cli.generate_dataset_stream.run_quantized_inference_batch')
    @patch('src.cli.generate_dataset_stream.calculate_gap')
    @patch('src.cli.generate_dataset_stream.load_quantized_model')
    @patch('src.cli.generate_dataset_stream.setup_logger')
    @patch('src.cli.generate_dataset_stream.ensure_log_dir')
    @patch('src.cli.generate_dataset_stream.log_sample_progress')
    def test_main_creates_parquet_file(
        self, mock_log_progress, mock_ensure_log, mock_logger, mock_load_model,
        mock_calc_gap, mock_run_infer, mock_extract_features, mock_load_ds, temp_output_dir
    ):
        """Test that main() creates the output parquet file with expected schema."""
        # Mock dataset
        mock_ds = [
            {"question_id": "1", "question": "What is 2+2?"},
            {"question_id": "2", "question": "What is 3+3?"}
        ]
        mock_load_ds.return_value = mock_ds

        # Mock feature extraction
        mock_extract_features.return_value = {
            "logits": [0.1, 0.2, 0.3],
            "gradient_norms": 0.5,
            "local_curvature": 0.2
        }

        # Mock inference
        mock_run_infer.return_value = [{"logits": [0.1, 0.2, 0.3]}]

        # Mock gap calculation
        mock_calc_gap.return_value = 0.05

        # Mock model loading
        mock_load_model.return_value = MagicMock()

        # Mock config
        with patch('src.cli.generate_dataset_stream.load_config') as mock_config:
            mock_config.return_value = {"dataset_id": "gsm8k"}

            # Change output dir for test
            with patch('src.cli.generate_dataset_stream.OUTPUT_DIR', Path(temp_output_dir)):
                with patch('src.cli.generate_dataset_stream.OUTPUT_FILE', Path(temp_output_dir) / "training_sample.parquet"):
                    main()

        # Verify output file exists
        output_file = Path(temp_output_dir) / "training_sample.parquet"
        assert output_file.exists(), "Output parquet file was not created"

        # Verify content
        df = pd.read_parquet(output_file)
        assert len(df) == 2, "Expected 2 rows in the output"
        assert "sample_id" in df.columns
        assert "prompt" in df.columns
        assert "quantized_logits" in df.columns
        assert "calculated_kl_divergence" in df.columns

    @patch('src.cli.generate_dataset_stream.load_dataset_streaming')
    def test_load_dataset_streaming_success(self, mock_load_ds):
        """Test that load_dataset_streaming correctly calls datasets.load_dataset."""
        mock_ds = MagicMock()
        mock_load_ds.return_value = mock_ds

        result = load_dataset_streaming("gsm8k")

        mock_load_ds.assert_called_once_with("gsm8k", split="train", streaming=True)
        assert result == mock_ds

    def test_process_single_sample_empty_prompt(self):
        """Test that process_single_sample returns None for empty prompts."""
        sample = {"question_id": "1", "question": ""}
        result = process_single_sample(sample, {})
        assert result is None

    @patch('src.cli.generate_dataset_stream.extract_features_for_sample')
    def test_process_single_sample_feature_extraction_failure(self, mock_extract):
        """Test that process_single_sample returns None if feature extraction fails."""
        mock_extract.return_value = None
        sample = {"question_id": "1", "question": "Test"}
        result = process_single_sample(sample, {})
        assert result is None