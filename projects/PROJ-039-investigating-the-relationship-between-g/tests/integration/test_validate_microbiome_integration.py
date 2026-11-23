"""
Integration test for validate_microbiome_fields script.
"""
import pytest
import tempfile
import os
import json
import subprocess
from pathlib import Path
import pandas as pd

def test_validate_microbiome_script_execution():
    """Test that the validation script runs and produces expected output."""
    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a valid CSV file
        valid_data = {
            'Age': [25, 30, 35, 40],
            'Sex': ['M', 'F', 'M', 'F'],
            'BMI': [22.5, 24.1, 23.0, 25.5],
            'Diet': ['Ve', 'Om', 'Ve', 'Ve']
        }
        valid_csv = tmpdir / 'valid_microbiome.csv'
        pd.DataFrame(valid_data).to_csv(valid_csv, index=False)
        
        # Run the validation script
        script_path = Path(__file__).parent.parent.parent / 'code' / 'validate_microbiome_fields.py'
        output_report = tmpdir / 'validation_report.json'
        
        result = subprocess.run(
            ['python', str(script_path), '--input', str(valid_csv), '--output', str(output_report)],
            capture_output=True,
            text=True
        )
        
        # Check script execution
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert output_report.exists(), "Output report not created"
        
        # Verify report content
        with open(output_report, 'r') as f:
            report = json.load(f)
        
        assert report['total_rows'] == 4
        assert report['valid_rows'] == 4
        assert report['invalid_rows'] == 0
        for field in ['Age', 'Sex', 'BMI', 'Diet']:
            assert report['missing_fields'][field] == 0

def test_validate_microbiome_script_with_errors():
    """Test that the validation script detects missing fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a CSV with missing fields
        invalid_data = {
            'Age': [25, 30, 35],
            'Sex': ['M', 'F', 'M'],
            'BMI': [22.5, 24.1, None],  # Missing BMI in last row
            'Diet': ['Ve', 'Om', 'Ve']
        }
        invalid_csv = tmpdir / 'invalid_microbiome.csv'
        pd.DataFrame(invalid_data).to_csv(invalid_csv, index=False)
        
        # Run the validation script
        script_path = Path(__file__).parent.parent.parent / 'code' / 'validate_microbiome_fields.py'
        output_report = tmpdir / 'validation_report.json'
        
        result = subprocess.run(
            ['python', str(script_path), '--input', str(invalid_csv), '--output', str(output_report)],
            capture_output=True,
            text=True
        )
        
        # Check script execution (should succeed but with warnings)
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert output_report.exists(), "Output report not created"
        
        # Verify report content
        with open(output_report, 'r') as f:
            report = json.load(f)
        
        assert report['total_rows'] == 3
        assert report['valid_rows'] == 2
        assert report['invalid_rows'] == 1
        assert report['missing_fields']['BMI'] == 1
