import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add parent to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.evaluate import calculate_stability_and_flip_rate

class TestSensitivityStability:
    """Unit tests for T027 stability calculation and flip rate logic."""

    @pytest.fixture
    def temp_sensitivity_raw(self):
        """Create a temporary sensitivity raw CSV file for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "sensitivity_sweep_raw.csv"
            
            # Create test data with known flip behavior
            # Dimension A: No flips (status constant)
            # Dimension B: 1 flip (status changes once)
            # Dimension C: 2 flips (status changes twice)
            data = {
                'dimension': ['DimA', 'DimA', 'DimA', 
                              'DimB', 'DimB', 'DimB',
                              'DimC', 'DimC', 'DimC'],
                'threshold': [0.80, 0.85, 0.90,
                              0.80, 0.85, 0.90,
                              0.80, 0.85, 0.90],
                'status': ['feature-sufficient', 'feature-sufficient', 'feature-sufficient',
                           'feature-sufficient', 'VLM-required', 'VLM-required',
                           'feature-sufficient', 'VLM-required', 'feature-sufficient']
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)
            
            yield input_path

    def test_flip_rate_calculation(self, temp_sensitivity_raw):
        """Test that flip rates are calculated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity_analysis.csv"
            
            result_df = calculate_stability_and_flip_rate(
                sensitivity_raw_path=str(temp_sensitivity_raw),
                output_path=str(output_path)
            )
            
            # Verify output file exists
            assert output_path.exists(), "Output CSV file was not created"
            
            # Verify required columns exist
            required_cols = ['dimension', 'threshold', 'status', 'flip_rate']
            assert all(col in result_df.columns for col in required_cols), \
                f"Missing required columns. Found: {result_df.columns.tolist()}"
            
            # Check flip rates
            # DimA: 0 flips out of 2 transitions -> 0.0
            dim_a = result_df[result_df['dimension'] == 'DimA']
            assert all(dim_a['flip_rate'] == 0.0), "DimA should have flip_rate 0.0"
            
            # DimB: 1 flip out of 2 transitions -> 0.5
            dim_b = result_df[result_df['dimension'] == 'DimB']
            assert all(dim_b['flip_rate'] == 0.5), "DimB should have flip_rate 0.5"
            
            # DimC: 2 flips out of 2 transitions -> 1.0
            dim_c = result_df[result_df['dimension'] == 'DimC']
            assert all(dim_c['flip_rate'] == 1.0), "DimC should have flip_rate 1.0"

    def test_threshold_sensitive_flag(self, temp_sensitivity_raw):
        """Test that threshold_sensitive flag is set correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity_analysis.csv"
            
            result_df = calculate_stability_and_flip_rate(
                sensitivity_raw_path=str(temp_sensitivity_raw),
                output_path=str(output_path)
            )
            
            # Check threshold_sensitive flag
            # DimA (flip_rate=0.0) -> False
            dim_a = result_df[result_df['dimension'] == 'DimA']
            assert all(~dim_a['threshold_sensitive']), "DimA should not be threshold_sensitive"
            
            # DimB (flip_rate=0.5) -> True
            dim_b = result_df[result_df['dimension'] == 'DimB']
            assert all(dim_b['threshold_sensitive']), "DimB should be threshold_sensitive"
            
            # DimC (flip_rate=1.0) -> True
            dim_c = result_df[result_df['dimension'] == 'DimC']
            assert all(dim_c['threshold_sensitive']), "DimC should be threshold_sensitive"

    def test_output_file_format(self, temp_sensitivity_raw):
        """Test that output file is written correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity_analysis.csv"
            
            result_df = calculate_stability_and_flip_rate(
                sensitivity_raw_path=str(temp_sensitivity_raw),
                output_path=str(output_path)
            )
            
            # Read back and verify
            reloaded = pd.read_csv(output_path)
            
            assert len(reloaded) == 9, "Expected 9 rows (3 dims x 3 thresholds)"
            assert 'dimension' in reloaded.columns
            assert 'threshold' in reloaded.columns
            assert 'status' in reloaded.columns
            assert 'flip_rate' in reloaded.columns

    def test_missing_input_file(self):
        """Test that FileNotFoundError is raised for missing input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent = Path(tmpdir) / "non_existent.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            with pytest.raises(FileNotFoundError):
                calculate_stability_and_flip_rate(
                    sensitivity_raw_path=str(non_existent),
                    output_path=str(output_path)
                )

    def test_invalid_input_columns(self):
        """Test that ValueError is raised for missing required columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "invalid.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Create file with wrong columns
            pd.DataFrame({'dim': ['A'], 'thresh': [0.8]}).to_csv(input_path, index=False)
            
            with pytest.raises(ValueError):
                calculate_stability_and_flip_rate(
                    sensitivity_raw_path=str(input_path),
                    output_path=str(output_path)
                )