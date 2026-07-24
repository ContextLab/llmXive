"""
Integration test for T017: Generate standardized CSV output with checksums.

Verifies that:
1. The script runs without error.
2. data/processed/standardized.csv is created.
3. The CSV contains the required columns.
4. The checksum file is created and valid.
"""
import hashlib
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.generate_standardized_output import (
    compute_sha256,
    validate_schema,
    REQUIRED_COLUMNS
)

class TestT017SchemaValidation:
    def test_validate_schema_pass(self):
        """Test that a DataFrame with required columns passes."""
        df = pd.DataFrame({
            'participant_id': [1],
            'stimulus_sequence': ['A'],
            'duration_estimate': [100.0],
            'surprisal': [0.5]
        })
        assert validate_schema(df) is True

    def test_validate_schema_fail_missing_column(self):
        """Test that a DataFrame missing a column fails."""
        df = pd.DataFrame({
            'participant_id': [1],
            'stimulus_sequence': ['A'],
            'duration_estimate': [100.0]
            # 'surprisal' missing
        })
        assert validate_schema(df) is False

class TestT017Checksum:
    def test_compute_sha256(self, tmp_path):
        """Test checksum computation on a known string."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        
        checksum = compute_sha256(test_file)
        expected = hashlib.sha256(content.encode()).hexdigest()
        
        assert checksum == expected

class TestT017Integration:
    @pytest.fixture(autouse=True)
    def setup_mock_data(self, tmp_path):
        """Mock the preprocessing pipeline to return valid data."""
        # Create a mock dataframe
        mock_data = pd.DataFrame({
            'participant_id': [1, 2, 3],
            'stimulus_sequence': ['A', 'B', 'A'],
            'duration_estimate': [100.0, 200.0, 150.0],
            'surprisal': [0.1, 0.2, 0.3]
        })
        
        # Patch run_preprocessing_pipeline
        with patch('code.generate_standardized_output.run_preprocessing_pipeline', return_value=mock_data):
            # Patch get_data_dir to use temp directory
            with patch('code.generate_standardized_output.get_data_dir', return_value=tmp_path):
                yield tmp_path

    def test_t017_creates_files(self, setup_mock_data):
        """Test that T017 creates the expected output files."""
        from code.generate_standardized_output import run_t017
        
        # Run the task
        result = run_t017()
        
        assert result is True
        
        output_csv = setup_mock_data / "processed" / "standardized.csv"
        checksum_file = setup_mock_data / "processed" / "standardized.csv.sha256"
        
        assert output_csv.exists(), "standardized.csv was not created"
        assert checksum_file.exists(), "checksum file was not created"

    def test_t017_output_content(self, setup_mock_data):
        """Test that the output CSV contains valid data."""
        from code.generate_standardized_output import run_t017
        
        run_t017()
        
        output_csv = setup_mock_data / "processed" / "standardized.csv"
        df = pd.read_csv(output_csv)
        
        assert len(df) == 3, "Row count mismatch"
        for col in REQUIRED_COLUMNS:
            assert col in df.columns, f"Missing column: {col}"

    def test_t017_checksum_valid(self, setup_mock_data):
        """Test that the generated checksum matches the file content."""
        from code.generate_standardized_output import run_t017
        
        run_t017()
        
        output_csv = setup_mock_data / "processed" / "standardized.csv"
        checksum_file = setup_mock_data / "processed" / "standardized.csv.sha256"
        
        # Read stored checksum
        stored_checksum = checksum_file.read_text().split()[0]
        
        # Compute actual checksum
        actual_checksum = compute_sha256(output_csv)
        
        assert stored_checksum == actual_checksum, "Checksum mismatch"
