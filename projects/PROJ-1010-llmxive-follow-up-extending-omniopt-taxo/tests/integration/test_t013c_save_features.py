"""
Integration test for T013c: Verify that the extraction script runs and produces a valid CSV.
This test mocks the heavy computation parts to ensure the file I/O logic works correctly
without requiring a full GPU run in the test environment.
"""
import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

from extract_and_save_spectral_features import save_features_to_csv, main
from utils.logging import configure_logging


def test_save_features_to_csv():
    """Test that save_features_to_csv creates a valid CSV with correct headers."""
    configure_logging()

    # Mock data
    mock_features = [
        {
            "model_id": "test-model-1",
            "architecture": "ResNet",
            "param_count": 12000000,
            "spectral_radius": 1.5,
            "condition_number": 10.2,
            "tail_decay_exponent": 2.1,
            "spectral_entropy": 4.5,
            "status": "success",
            "timestamp": "2023-10-27T10:00:00Z",
        },
        {
            "model_id": "test-model-2",
            "architecture": "ViT",
            "param_count": 85000000,
            "spectral_radius": 2.0,
            "condition_number": 15.5,
            "tail_decay_exponent": 1.8,
            "spectral_entropy": 5.1,
            "status": "success",
            "timestamp": "2023-10-27T10:05:00Z",
        },
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_features.csv"
        
        # Execute
        save_features_to_csv(mock_features, output_path)

        # Verify file exists
        assert output_path.exists(), "Output CSV file was not created."

        # Verify content
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
        
        # Check headers
        expected_headers = [
            "model_id", "architecture", "param_count", 
            "spectral_radius", "condition_number", 
            "tail_decay_exponent", "spectral_entropy", 
            "status", "timestamp"
        ]
        assert reader.fieldnames == expected_headers, f"Headers mismatch: {reader.fieldnames}"

        # Check data integrity
        assert rows[0]["model_id"] == "test-model-1"
        assert float(rows[0]["spectral_radius"]) == 1.5
        assert rows[1]["architecture"] == "ViT"


def test_main_with_mocked_computation():
    """
    Test the main() function by mocking the heavy lifting (model selection and training).
    This ensures the script flow and file writing work without a real GPU run.
    """
    configure_logging()

    mock_models = [
        {"model_id": "mock-model", "architecture": "MockNet", "model_name": "mock/name"}
    ]
    
    mock_training_result = {
        "gradients": [1.0, 2.0, 3.0], # Mock gradient data
        "covariance": [[1.0, 0.1], [0.1, 2.0]] # Mock covariance
    }

    mock_features = {
        "spectral_radius": 1.2,
        "condition_number": 5.0,
        "tail_decay_exponent": 1.5,
        "spectral_entropy": 3.2
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch paths and functions
        with patch("extract_and_save_spectral_features.select_models", return_value=mock_models), \
             patch("extract_and_save_spectral_features.run_proxy_training", return_value=mock_training_result), \
             patch("extract_and_save_spectral_features.compute_spectral_features", return_value=mock_features), \
             patch("extract_and_save_spectral_features.count_parameters", return_value=1000000), \
             patch("extract_and_save_spectral_features.DATA_PROCESSED_DIR", Path(tmpdir)), \
             patch("extract_and_save_spectral_features.OUTPUT_FILE", Path(tmpdir) / "spectral_features.csv"):

            result = main()

            # Verify success
            assert result == 0, "Main function returned non-zero exit code."
            
            # Verify file was created
            output_file = Path(tmpdir) / "spectral_features.csv"
            assert output_file.exists(), "Output file was not created by main()."

            with open(output_file, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 1, "Expected 1 row in output."
            assert rows[0]["model_id"] == "mock-model"
            assert rows[0]["status"] == "success"