"""
Unit tests for the data loader and verification gate.
"""
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.loader import verify_clinical_columns, run_data_availability_gate

class TestClinicalColumnVerification:
    """Tests for verify_clinical_columns function."""

    def test_all_columns_present(self):
        """Test that verification passes when all required columns are present."""
        df = pd.DataFrame({
            "SampleID": ["S1"],
            "BMI": [25.0],
            "Glucose": [90.0],
            "BP_Systolic": [120.0],
            "BP_Diastolic": [80.0],
            "Triglycerides": [150.0],
            "HDL_Cholesterol": [50.0]
        })
        
        is_valid, missing = verify_clinical_columns(df)
        assert is_valid is True
        assert len(missing) == 0

    def test_missing_bmi(self):
        """Test that verification fails when BMI is missing."""
        df = pd.DataFrame({
            "SampleID": ["S1"],
            "Glucose": [90.0],
            "BP_Systolic": [120.0],
            "BP_Diastolic": [80.0],
            "Triglycerides": [150.0],
            "HDL_Cholesterol": [50.0]
        })
        
        is_valid, missing = verify_clinical_columns(df)
        assert is_valid is False
        assert "BMI" in missing

    def test_missing_glucose(self):
        """Test that verification fails when Glucose is missing."""
        df = pd.DataFrame({
            "SampleID": ["S1"],
            "BMI": [25.0],
            "BP_Systolic": [120.0],
            "BP_Diastolic": [80.0],
            "Triglycerides": [150.0],
            "HDL_Cholesterol": [50.0]
        })
        
        is_valid, missing = verify_clinical_columns(df)
        assert is_valid is False
        assert "Glucose" in missing

    def test_missing_bp(self):
        """Test that verification fails when BP columns are missing."""
        df = pd.DataFrame({
            "SampleID": ["S1"],
            "BMI": [25.0],
            "Glucose": [90.0],
            "Triglycerides": [150.0],
            "HDL_Cholesterol": [50.0]
        })
        
        is_valid, missing = verify_clinical_columns(df)
        assert is_valid is False
        assert "BP" in missing

    def test_missing_triglycerides(self):
        """Test that verification fails when Triglycerides is missing."""
        df = pd.DataFrame({
            "SampleID": ["S1"],
            "BMI": [25.0],
            "Glucose": [90.0],
            "BP_Systolic": [120.0],
            "BP_Diastolic": [80.0],
            "HDL_Cholesterol": [50.0]
        })
        
        is_valid, missing = verify_clinical_columns(df)
        assert is_valid is False
        assert "Triglycerides" in missing

    def test_missing_hdl(self):
        """Test that verification fails when HDL_Cholesterol is missing."""
        df = pd.DataFrame({
            "SampleID": ["S1"],
            "BMI": [25.0],
            "Glucose": [90.0],
            "BP_Systolic": [120.0],
            "BP_Diastolic": [80.0],
            "Triglycerides": [150.0]
        })
        
        is_valid, missing = verify_clinical_columns(df)
        assert is_valid is False
        assert "HDL_Cholesterol" in missing

    def test_multiple_missing_columns(self):
        """Test that all missing columns are reported."""
        df = pd.DataFrame({
            "SampleID": ["S1"]
        })
        
        is_valid, missing = verify_clinical_columns(df)
        assert is_valid is False
        assert "BMI" in missing
        assert "Glucose" in missing
        assert "BP" in missing
        assert "Triglycerides" in missing
        assert "HDL_Cholesterol" in missing

class TestDataAvailabilityGate:
    """Tests for run_data_availability_gate function."""

    def test_gate_passes_with_complete_data(self, tmp_path):
        """Test that gate passes and returns True when data is complete."""
        df = pd.DataFrame({
            "SampleID": ["S1"],
            "BMI": [25.0],
            "Glucose": [90.0],
            "BP_Systolic": [120.0],
            "BP_Diastolic": [80.0],
            "Triglycerides": [150.0],
            "HDL_Cholesterol": [50.0]
        })
        
        result = run_data_availability_gate(df, tmp_path)
        assert result is True

    def test_gate_writes_failure_json(self, tmp_path, caplog):
        """Test that gate writes JSON file and exits on missing data."""
        import sys
        from io import StringIO
        
        df = pd.DataFrame({
            "SampleID": ["S1"],
            "BMI": [25.0]
            # Missing Glucose, BP, TG, HDL
        })
        
        # Capture sys.exit call
        with pytest.raises(SystemExit) as excinfo:
            run_data_availability_gate(df, tmp_path)
        
        assert excinfo.value.code == 1
        
        # Check that JSON file was written
        gate_file = tmp_path / "data_availability_gate.json"
        assert gate_file.exists()
        
        with open(gate_file, 'r') as f:
            gate_data = json.load(f)
        
        assert gate_data["status"] == "Exploratory - Insufficient Phenotype Data"
        assert "missing_columns" in gate_data
        assert len(gate_data["missing_columns"]) > 0

    def test_gate_exits_on_missing_data(self, tmp_path):
        """Test that gate exits with code 1 when data is missing."""
        df = pd.DataFrame({
            "SampleID": ["S1"],
            "BMI": [25.0]
        })
        
        with pytest.raises(SystemExit) as excinfo:
            run_data_availability_gate(df, tmp_path)
        
        assert excinfo.value.code == 1