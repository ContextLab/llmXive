"""
Unit tests for the export_descriptors module (T020a).
"""

import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.features.export_descriptors import (
    load_processed_data,
    calculate_and_export_descriptors,
    main
)
from code.data.models import MaterialType
from code.features.mass_balance import validate_descriptor_mass_balance

class TestLoadProcessedData:
    def test_load_success(self, tmp_path):
        """Test loading a valid parquet file."""
        # Create a mock parquet file
        data = {
            'sample_id': ['s1', 's1', 's2'],
            'material': ['Al', 'Al', 'Cu'],
            'reduction': [20, 20, 40],
            'phi1': [0.0, 10.0, 5.0],
            'Phi': [45.0, 46.0, 45.0],
            'phi2': [90.0, 91.0, 90.0],
            'confidence': [0.9, 0.8, 0.95]
        }
        df = pd.DataFrame(data)
        parquet_path = tmp_path / "cleaned_ebsd.parquet"
        df.to_parquet(parquet_path)

        loaded_df = load_processed_data(str(parquet_path))
        assert len(loaded_df) == 3
        assert 'sample_id' in loaded_df.columns

    def test_load_missing_file(self, tmp_path):
        """Test loading a non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_processed_data(str(tmp_path / "nonexistent.parquet"))

    def test_load_empty_file(self, tmp_path):
        """Test loading an empty file."""
        data = {
            'sample_id': [],
            'material': [],
            'reduction': [],
            'phi1': [],
            'Phi': [],
            'phi2': [],
            'confidence': []
        }
        df = pd.DataFrame(data)
        parquet_path = tmp_path / "empty.parquet"
        df.to_parquet(parquet_path)

        with pytest.raises(ValueError, match="empty"):
            load_processed_data(str(parquet_path))

    def test_load_missing_columns(self, tmp_path):
        """Test loading a file with missing required columns."""
        data = {
            'sample_id': ['s1'],
            'material': ['Al'],
            # Missing reduction, phi1, etc.
        }
        df = pd.DataFrame(data)
        parquet_path = tmp_path / "bad_cols.parquet"
        df.to_parquet(parquet_path)

        with pytest.raises(ValueError, match="missing required columns"):
            load_processed_data(str(parquet_path))

class TestCalculateAndExportDescriptors:
    @pytest.fixture
    def mock_descriptors(self):
        """Mock the calculate_descriptors function to return valid data."""
        with patch('code.features.export_descriptors.calculate_descriptors') as mock_calc:
            mock_calc.return_value = {
                'brass': 0.2,
                'copper': 0.3,
                's': 0.1,
                'goss': 0.1,
                'texture_index': 1.5,
                'random_fraction': 0.3
            }
            yield mock_calc

    @pytest.fixture
    def mock_mass_balance_valid(self):
        """Mock mass balance validation to pass."""
        with patch('code.features.export_descriptors.validate_descriptor_mass_balance') as mock_mb:
            mock_mb.return_value = (True, "OK")
            yield mock_mb

    def test_export_success(self, tmp_path, mock_descriptors, mock_mass_balance_valid):
        """Test successful export of descriptors."""
        # Create input data
        data = {
            'sample_id': ['s1', 's1', 's2'],
            'material': ['Al', 'Al', 'Cu'],
            'reduction': [20, 20, 40],
            'phi1': [0.0, 10.0, 5.0],
            'Phi': [45.0, 46.0, 45.0],
            'phi2': [90.0, 91.0, 90.0],
            'confidence': [0.9, 0.8, 0.95]
        }
        input_df = pd.DataFrame(data)
        input_path = tmp_path / "cleaned_ebsd.parquet"
        input_df.to_parquet(input_path)

        output_path = tmp_path / "descriptors.csv"

        result_df = calculate_and_export_descriptors(
            input_path=str(input_path),
            output_path=str(output_path)
        )

        assert result_df is not None
        assert len(result_df) == 2 # s1 and s2
        assert 'sample_id' in result_df.columns
        assert 'brass' in result_df.columns
        assert result_df['sample_id'].iloc[0] == 's1'
        assert result_df['sample_id'].iloc[1] == 's2'

        # Verify file was written
        assert output_path.exists()
        written_df = pd.read_csv(output_path)
        assert len(written_df) == 2

    def test_export_excludes_failed_mass_balance(self, tmp_path, mock_descriptors):
        """Test that samples failing mass balance are excluded."""
        # Mock mass balance to fail for sample 's2'
        def side_effect(**kwargs):
            # Simulate failure for specific sample if we could identify it,
            # but here we just make one call fail.
            # Since we can't easily distinguish calls in this simple mock,
            # we'll just make the second call fail if we track it.
            # A better way is to patch the specific logic inside the loop,
            # but for this test, let's assume the first call passes, second fails.
            # We'll use a counter.
            if not hasattr(side_effect, 'count'):
                side_effect.count = 0
            side_effect.count += 1
            
            if side_effect.count == 2:
                return (False, "Mass balance failed")
            return (True, "OK")

        with patch('code.features.export_descriptors.validate_descriptor_mass_balance', side_effect=side_effect):
            data = {
                'sample_id': ['s1', 's1', 's2'],
                'material': ['Al', 'Al', 'Cu'],
                'reduction': [20, 20, 40],
                'phi1': [0.0, 10.0, 5.0],
                'Phi': [45.0, 46.0, 45.0],
                'phi2': [90.0, 91.0, 90.0],
                'confidence': [0.9, 0.8, 0.95]
            }
            input_df = pd.DataFrame(data)
            input_path = tmp_path / "cleaned_ebsd.parquet"
            input_df.to_parquet(input_path)

            output_path = tmp_path / "descriptors.csv"

            result_df = calculate_and_export_descriptors(
                input_path=str(input_path),
                output_path=str(output_path)
            )

            # Only s1 should be present
            assert len(result_df) == 1
            assert result_df['sample_id'].iloc[0] == 's1'

    def test_export_no_valid_samples(self, tmp_path, mock_descriptors):
        """Test that an error is raised if no valid samples remain."""
        # Mock mass balance to fail for all
        with patch('code.features.export_descriptors.validate_descriptor_mass_balance', return_value=(False, "Failed")):
            data = {
                'sample_id': ['s1', 's1'],
                'material': ['Al', 'Al'],
                'reduction': [20, 20],
                'phi1': [0.0, 10.0],
                'Phi': [45.0, 46.0],
                'phi2': [90.0, 91.0],
                'confidence': [0.9, 0.8]
            }
            input_df = pd.DataFrame(data)
            input_path = tmp_path / "cleaned_ebsd.parquet"
            input_df.to_parquet(input_path)

            output_path = tmp_path / "descriptors.csv"

            with pytest.raises(RuntimeError, match="No valid samples found"):
                calculate_and_export_descriptors(
                    input_path=str(input_path),
                    output_path=str(output_path)
                )

class TestMain:
    @patch('code.features.export_descriptors.calculate_and_export_descriptors')
    @patch('code.features.export_descriptors.Path')
    def test_main_success(self, mock_path, mock_calc, tmp_path):
        """Test the main function execution."""
        # Mock path existence
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        mock_calc.return_value = pd.DataFrame({'sample_id': ['s1']})

        # Capture stdout
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            main()

        output = f.getvalue()
        assert "Successfully exported" in output or "Exported" in output

    @patch('code.features.export_descriptors.Path')
    def test_main_missing_input(self, mock_path):
        """Test main when input file is missing."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        with pytest.raises(SystemExit):
            main()