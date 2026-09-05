"""
Integration test for T016: Validation of baseline_results.csv.

Ensures that the validation logic correctly handles cases where
the model error exceeds 0.1 eV/atom, ensuring the file is still
valid and contains the required columns.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validate_baseline_results import validate_results_file, RESULTS_FILE, ERROR_THRESHOLD
from config import OUTPUTS_DIR

class TestT016Validation:
    
    def test_file_not_found(self):
        """Test behavior when the results file does not exist."""
        # Create a temporary non-existent path for testing
        fake_path = OUTPUTS_DIR / "non_existent_file.csv"
        result = validate_results_file(fake_path)
        
        assert result["exists"] is False
        assert result["valid"] is False
        assert "not found" in result["message"]

    def test_missing_columns(self):
        """Test behavior when required columns are missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("material_id,true_energy\n")
            f.write("1,2.5\n")
            temp_path = Path(f.name)
        
        try:
            result = validate_results_file(temp_path)
            assert result["valid"] is False
            assert "Missing required columns" in result["message"]
        finally:
            temp_path.unlink()

    def test_empty_dataframe(self):
        """Test behavior when the CSV is empty."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("material_id,true_energy,predicted_energy,mae,rmse\n")
            temp_path = Path(f.name)
        
        try:
            result = validate_results_file(temp_path)
            assert result["valid"] is False
            assert "empty" in result["message"].lower()
        finally:
            temp_path.unlink()

    def test_high_error_preserved(self):
        """
        Critical Test: Ensure file is valid even if error > 0.1 eV/atom.
        This is the core requirement of T016.
        """
        # Create a dataset with high error
        data = {
            "material_id": ["m1", "m2", "m3"],
            "true_energy": [0.0, 1.0, 2.0],
            "predicted_energy": [0.5, 2.0, 3.5], # Errors: 0.5, 1.0, 1.5 -> Mean ~1.0 > 0.1
            "mae": [1.0, 1.0, 1.0], # Placeholder or repeated metric
            "rmse": [1.2, 1.2, 1.2]
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            temp_path = Path(f.name)
        
        try:
            result = validate_results_file(temp_path)
            
            # The file MUST be valid (exists, has columns, no NaN)
            assert result["exists"] is True
            assert result["valid"] is True
            
            # The high error flag MUST be set
            assert result["high_error_warning"] is True
            
            # The message should explicitly mention the threshold breach
            assert "exceeds threshold" in result["message"]
            
            # Verify the calculated MAE is indeed high
            assert result["calculated_mae"] > ERROR_THRESHOLD
            
        finally:
            temp_path.unlink()

    def test_acceptable_error(self):
        """Test behavior when error is within acceptable range."""
        # Create a dataset with low error
        data = {
            "material_id": ["m1", "m2", "m3"],
            "true_energy": [0.0, 1.0, 2.0],
            "predicted_energy": [0.01, 1.01, 2.01], # Errors: 0.01, 0.01, 0.01 -> Mean 0.01
            "mae": [0.01, 0.01, 0.01],
            "rmse": [0.01, 0.01, 0.01]
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            temp_path = Path(f.name)
        
        try:
            result = validate_results_file(temp_path)
            
            assert result["exists"] is True
            assert result["valid"] is True
            assert result["high_error_warning"] is False
            assert result["calculated_mae"] <= ERROR_THRESHOLD
        finally:
            temp_path.unlink()

    def test_nan_values_rejected(self):
        """Test that NaN values in critical columns cause validation failure."""
        data = {
            "material_id": ["m1", "m2"],
            "true_energy": [0.0, 1.0],
            "predicted_energy": [0.5, float('nan')],
            "mae": [0.5, 0.5],
            "rmse": [0.6, 0.6]
        }
        df = pd.DataFrame(data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            temp_path = Path(f.name)
        
        try:
            result = validate_results_file(temp_path)
            assert result["valid"] is False
            assert "NaN" in result["message"]
        finally:
            temp_path.unlink()